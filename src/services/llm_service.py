import asyncio
import json
import re
import traceback
from typing import List, Dict, Any, Optional
import aiohttp
import requests
from src.config.settings import Config
from src.data.models.RealEstateModel import RealEstateProperty
from src.utils.logging import get_logger
from src.utils.text_processing import clean_text, extract_area, extract_bathrooms, extract_city_from_address, \
    extract_frontage, extract_price, extract_rooms, parse_date


class LLMService:
    """Service for processing property descriptions with LLM"""

    def __init__(self):
        self.logger = get_logger("llm_service")
        self.config = Config()
        self.api_token = self.config.LLM_API_TOKEN
        self.provider = self.config.LLM_PROVIDER
        self.batch_size = self.config.LLM_BATCH_SIZE
        self.enabled = self.config.LLM_ENABLED

        self.gemini_semaphore = asyncio.Semaphore(1)  # Limit concurrent Gemini requests
        # Property types mapping
        self.property_types = [
            "căn hộ", "nhà phố", "đất nền",
            "biệt thự", "shophouse", "kho xưởng"
        ]

    async def process_batch(self, properties: List[RealEstateProperty]) -> List[RealEstateProperty]:
        """Process a batch of properties with LLM"""
        print(">>> CALL LLM process_batch")
        if not self.enabled:
            self.logger.warning("LLM processing disabled or no API token")
            return properties

        try:
            # Split into smaller batches for processing
            processed_properties = []

            for i in range(0, len(properties), self.batch_size):
                batch = properties[i:i + self.batch_size]
                processed_batch = await self._process_single_batch(batch)
                processed_properties.extend(processed_batch)

                # Small delay between batches
                await asyncio.sleep(2)

            return processed_properties

        except Exception as e:
            self.logger.error(f"Error processing batch with LLM: {e}")
            return properties

    async def _process_single_batch(self, properties: List[RealEstateProperty]) -> List[RealEstateProperty]:
        """Process a single batch of properties"""
        FIELDS = [
            "title", "address", "price", "area", "unit_price", "seller", "bedroom", "bathroom",
            "frontage", "legal", "postedDate", "description", "link", "city", "amenityLocation", "type"
        ]
        try:
            # Prepare batch request
            batch_descriptions = []
            missing_fields_set = set()
            for prop in properties:
                desc = {field: getattr(prop, field, None) for field in FIELDS}
                desc['id'] = str(prop.id)
                batch_descriptions.append(desc)
                for field in FIELDS:
                    if not desc.get(field):
                        missing_fields_set.add(field)
            missing_fields = list(missing_fields_set)
            prompt = self._create_batch_prompt(batch_descriptions, missing_fields)

            # Call LLM API

            llm_response = await self._call_llm_api(prompt)

            if llm_response is not None:
                print(json.dumps(llm_response, ensure_ascii=False, indent=2))
            else:
                print("LLM RESPONSE IS NONE")

            if isinstance(llm_response, list) and len(llm_response) > 0:
                #     print(">>> [DEBUG] llm_response type:", type(llm_response), "length:", len(llm_response) if isinstance(llm_response, list) else "N/A")
                #     print(">>> [DEBUG] CALLING _update_properties_from_response")
                #     # Chỉ gọi update nếu là list và có phần tử
                self._update_properties_from_response(properties, llm_response)

            return properties

        except Exception as e:

            self.logger.error(f"Error processing single batch: {e}")
            return properties

    def _create_batch_prompt(self, descriptions: List[Dict[str, Any]], missing_fields: List[str]) -> str:
        property_types_str = ", ".join(self.property_types)
        prompt = f"""
    Bạn là chuyên gia bất động sản.
    Dưới đây là thông tin về một số bất động sản, mỗi bất động sản có 16 trường. Một số trường đã có giá trị, một số trường còn thiếu (giá trị là null hoặc rỗng).

    Hãy phân tích mô tả và điền giá trị cho các trường còn thiếu (giá trị là null hoặc rỗng) trong danh sách sau:
    {missing_fields}

    **YÊU CẦU:**
    - Chỉ trả về kết quả dưới dạng JSON array.
    - Mỗi object trong array BẮT BUỘC phải có trường "id" (giá trị giống như đầu vào).
    - Mỗi object chỉ gồm các trường còn thiếu (và id), không thêm text khác, không trả về các trường đã có giá trị, không tự ý thêm trường không có trong mục description, không tự suy diễn, không bịa hoặc dự đoán.
    - Nếu không thể xác định giá trị cho trường nào, hãy để giá trị là null( không trả về chuỗi rỗng)

    Quy tắc trích xuất legal:
    - Chỉ điền giá trị nếu thông tin pháp lý (sổ đỏ, sổ hồng, hợp đồng mua bán, giấy tờ tay, ...) thực sự xuất hiện trong mô tả.
    - Không tự suy diễn, không dự đoán, không bịa thông tin pháp lý nếu mô tả không đề cập.
    - Nếu không có thông tin pháp lý trong mô tả, hãy để giá trị là null (không trả về chuỗi rỗng).
    - Chỉ lấy đúng cụm từ xuất hiện trong mô tả, không dịch, không rút gọn.

    Quy tắc trích xuất amenityLocation:
    - Lấy những thông tin về tiện ích xung quanh bất động sản như trường học, bệnh viện, trung tâm thương mại, công viên, giao thông công cộng, khu dân cư đông đúc, những lợi ích khi ở đây ...
    - Trích xuất nguyên văn cụm từ xuất hiện trong mô tả.
    - Không tự suy diễn, không dự đoán, không bịa thông tin pháp lý nếu mô tả không đề cập.

    Quy tắc phân loại type:
    - căn hộ: chung cư, apartment, căn hộ cao cấp
    - nhà phố: nhà riêng, nhà phố, townhouse  
    - đất nền: đất thổ cư, đất nền, lô đất
    - biệt thự: villa, biệt thự, nhà vườn lớn
    - shophouse: nhà mặt phố kinh doanh, shophouse
    - kho xưởng: nhà xưởng, kho bãi, đất công nghiệp

    Dữ liệu đầu vào:
    """
        for i, desc in enumerate(descriptions, 1):
            prompt += f"""
    {i}. ID: {desc['id']}
    """
            for field, value in desc.items():
                if field != 'id':
                    prompt += f"{field}: {value}\n"
        return prompt

    async def _call_llm_api(self, prompt: str) -> Optional[Dict[str, Any]]:

        try:
            if 'gemini' in self.provider.lower():

                return await self._call_gemini_api(prompt)
            elif 'openai' in self.provider.lower():

                return await self._call_openai_api(prompt)
            else:
                self.logger.warning(f"Unsupported LLM provider: {self.provider}")
                return None
        except Exception as e:
            self.logger.error(f"Error calling LLM API: {e}")
            return None

    async def _call_openai_api(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Call OpenAI-compatible API (Ollama, LM Studio, etc.)"""
        try:
            url = f"{self.config.LLM_API_BASE_URL}/chat/completions"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_token}" if self.api_token else None
            }
            payload = {
                "model": "mistral",  # hoặc "phi", "llama3", ... tùy model bạn chạy
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1,
                "max_tokens": 2048
            }
            # Xóa header Authorization nếu không có token
            if not self.api_token:
                headers.pop("Authorization")
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        # Ollama/LM Studio trả về kết quả trong choices[0].message.content
                        content = result["choices"][0]["message"]["content"]
                        try:
                            start = content.find('[')
                            end = content.rfind(']') + 1
                            if start >= 0 and end > start:
                                json_str = content[start:end]
                                return json.loads(json_str)
                        except Exception as e:
                            self.logger.error(f"Error parsing JSON from LLM response: {e}")
                    else:
                        self.logger.error(f"OpenAI API error: {response.status}")
                        if response.status == 429:
                            await asyncio.sleep(10)
        except Exception as e:
            self.logger.error(f"Error calling OpenAI API: {e}")
        return None

    async def _call_gemini_api(self, prompt: str) -> Optional[Dict[str, Any]]:
        url = self.config.LLM_API_BASE_URL
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_token
        }
        payload = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 8192
            }
        }

        def sync_post():
            try:
                resp = requests.post(url, headers=headers, json=payload, timeout=30)

                if resp.status_code == 200:
                    result = resp.json()
                    if 'candidates' in result and result['candidates']:
                        text = result['candidates'][0]['content']['parts'][0]['text']

                        # Loại bỏ markdown code block nếu có
                        if text.strip().startswith("```"):
                            text = re.sub(r"^```[a-zA-Z]*\n?", "", text.strip())
                            text = re.sub(r"\n?```$", "", text.strip())

                        # Tìm JSON array trong text
                        matches = re.findall(r"\[.*\]", text, re.DOTALL)

                        if matches:
                            json_str = matches[0]
                            try:

                                return json.loads(json_str)
                            except Exception as e:
                                print("Exception parsing JSON from Gemini response:", e)

                        else:
                            print("NO JSON ARRAY FOUND IN TEXT:", text)
            except Exception as e:
                print("Exception in requests.post:", e)
                traceback.print_exc()
            return None

        result = sync_post()
        print(">>> [DEBUG] sync_post result:", result)
        return result

    def _update_properties_from_response(self, properties: List[RealEstateProperty],
                                         llm_response: List[Dict[str, Any]]):
        try:
            response_map = {str(item['id']): item for item in llm_response if 'id' in item}
            for prop in properties:
                prop_id = str(prop.id)
                if prop_id in response_map:
                    llm_data = response_map[prop_id]
                    # Luôn cập nhật các trường enrich từ LLM (không kiểm tra and not prop.xxx)
                    if 'title' in llm_data:
                        prop.title = clean_text(llm_data['title'])
                    if 'address' in llm_data:
                        prop.address = clean_text(llm_data['address'])
                    if 'area' in llm_data:
                        prop.area = extract_area(str(llm_data['area']))
                    if 'price' in llm_data:
                        prop.price = extract_price(str(llm_data['price']))
                    if 'unit_price' in llm_data:
                        prop.unit_price = extract_price(str(llm_data['unit_price']))
                    if (not prop.unit_price or prop.unit_price == 0) and prop.price and prop.area:
                        try:
                            prop.unit_price = round(prop.price / prop.area, 2)
                        except Exception:
                            prop.unit_price = None
                    if 'seller' in llm_data:
                        prop.seller = clean_text(llm_data['seller'])
                    if 'bedroom' in llm_data:
                        prop.bedroom = extract_rooms(str(llm_data['bedroom']))
                    if 'bathroom' in llm_data:
                        prop.bathroom = extract_bathrooms(str(llm_data['bathroom']))
                    if 'frontage' in llm_data:
                        prop.frontage = extract_frontage(str(llm_data['frontage']))
                    if 'legal' in llm_data:
                        prop.legal = clean_text(llm_data['legal'])
                    if 'postedDate' in llm_data:
                        date_obj = parse_date(llm_data['postedDate'])
                        prop.postedDate = date_obj.strftime('%d/%m/%Y') if date_obj else None
                    if 'description' in llm_data:
                        prop.description = clean_text(llm_data['description'])
                    if 'link' in llm_data:
                        prop.link = clean_text(llm_data['link'])
                    if 'city' in llm_data:
                        prop.city = extract_city_from_address(llm_data['city']) if llm_data['city'] else None
                    if 'amenityLocation' in llm_data:
                        prop.amenityLocation = clean_text(llm_data['amenityLocation'])
                    if 'type' in llm_data:
                        prop_type = llm_data['type']
                        if prop_type:
                            prop_type = prop_type.lower()
                            if prop_type in self.property_types:
                                prop.type = prop_type
                            else:
                                for allowed_type in self.property_types:
                                    if allowed_type in prop_type or prop_type in allowed_type:
                                        prop.type = allowed_type
                                        break
                                else:
                                    prop.type = "căn hộ"
                        else:
                            prop.type = None
        except Exception as e:
            self.logger.error(f"Error updating properties from LLM response: {e}")


# Global instance
llm_service = LLMService()