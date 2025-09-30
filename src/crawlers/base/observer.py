from abc import ABC, abstractmethod
import asyncio
from typing import Any
from src.config.settings import Config
from src.data.models.RealEstateModel import RealEstateProperty


class CrawlerObserver(ABC):
    """Abstract observer for crawler events"""

    @abstractmethod
    def notify(self, event_type: str, data: Any, source: str):
        """Handle crawler notifications"""
        pass


class DataSaveObserver(CrawlerObserver):
    """Observer for saving data to database"""

    def __init__(self, repository):
        self.repository = repository

    def notify(self, event_type: str, data: Any, source: str):
        # print(f"[DataSaveObserver] notify called with event: {event_type}, data={data}")
        if event_type == "property_enriched":
            try:
                # print(f"[DataSaveObserver] Saving property: {getattr(data, 'link', None)}")
                self.repository.save_property(data)
            except Exception as e:
                print(f"[DataSaveObserver] Error saving property: {e}")
        elif event_type == "crawl_completed":
            try:
                self.repository.save_crawl_stats(data)
            except Exception as e:
                print(f"[DataSaveObserver] Error saving crawl stats: {e}")


class LoggingObserver(CrawlerObserver):
    """Observer for logging crawler events"""

    def __init__(self, logger):
        self.logger = logger

    def notify(self, event_type: str, data: Any, source: str):
        if event_type == "crawl_started":
            self.logger.info(f"[{source}] Crawl started")
        elif event_type == "property_extracted":
            self.logger.debug(f"[{source}] Property extracted: {data.title}")
        elif event_type == "crawl_completed":
            self.logger.info(f"[{source}] Crawl completed: {data.successful_items} successful")
        elif event_type == "crawl_failed":
            self.logger.error(f"[{source}] Crawl failed: {data['error']}")


class ProgressObserver(CrawlerObserver):
    """Observer for tracking crawl progress"""

    def __init__(self):
        self.progress = {}

    def notify(self, event_type: str, data: Any, source: str):
        if source not in self.progress:
            self.progress[source] = {
                'status': 'idle',
                'total_items': 0,
                'processed_items': 0,
                'start_time': None,
                'end_time': None
            }

        if event_type == "crawl_started":
            self.progress[source].update({
                'status': 'running',
                'start_time': data.start_time,
                'processed_items': 0
            })
        elif event_type == "property_extracted":
            self.progress[source]['processed_items'] += 1
        elif event_type == "crawl_completed":
            self.progress[source].update({
                'status': 'completed',
                'total_items': data.total_items,
                'end_time': data.end_time
            })
        elif event_type == "crawl_failed":
            self.progress[source].update({
                'status': 'failed',
                'end_time': data['stats'].end_time
            })

    def get_progress(self, source: str = None):
        """Get progress for specific source or all sources"""
        if source:
            return self.progress.get(source, {})
        return self.progress


class LLMProcessingObserver(CrawlerObserver):
    def __init__(self, llm_service, downstream_observers=None):
        config = Config()
        self.llm_service = llm_service
        self.batch = []
        self.batch_size = config.LLM_BATCH_SIZE
        self.downstream_observers = downstream_observers or []
        self.tasks = []  # Thêm dòng này

    def notify(self, event_type: str, data: Any, source: str):
        if event_type == "property_extracted":
            self.batch.append(data)
            if len(self.batch) >= self.batch_size:
                task = asyncio.create_task(self._process_batch(source))
                self.tasks.append(task)
        elif event_type == "crawl_completed":
            if self.batch:
                task = asyncio.create_task(self._process_batch(source))
                self.tasks.append(task)

    async def _process_batch(self, source):

        if self.batch:

            enriched = await self.llm_service.process_batch(self.batch)
            # Thêm dòng này
            for prop in enriched:
                if isinstance(prop, dict):
                    try:
                        prop = RealEstateProperty(**prop)
                    except Exception as e:
                        print(f"[LLM SERVICE] Error creating RealEstateProperty: {e}")
                        continue
                for obs in self.downstream_observers:
                    obs.notify("property_enriched", prop, source)
            self.batch = []
