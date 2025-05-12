import scrapy
from scrapy.crawler import CrawlerProcess
from urllib.parse import urljoin
import os
from pathlib import Path
from datetime import datetime
from .models import Answer

class SiteSpider(scrapy.Spider):
    name = "site"
    download_dir = "/app/data"  # Docker volume path

    def __init__(self, username, user_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.username = username
        self.user_id = user_id
        self.download_dir = os.path.join(self.download_dir, f"{username}_{user_id}", "downloads")
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)
        # Move answers logic here
        answers = Answer.objects.filter(user=self.user_id)
        self.answer_text = str(answers[0].response) if answers.exists() else ""
        self.start_urls = [self.answer_text] if self.answer_text else []

    def parse(self, response):
        content_type = response.headers.get("Content-Type", b"").decode().lower()
        
        if "text/html" in content_type:
            text = response.xpath("//body//text()").getall()
            clean_text = " ".join(t.strip() for t in text if t.strip())
            yield {
                "url": response.url,
                "text": clean_text,
                "type": "html",
                "timestamp": datetime.utcnow().isoformat()
            }

            for href in response.css("a::attr(href)").getall():
                if any(href.lower().endswith(ext) for ext in [".pdf", ".doc", ".docx", ".xls", ".xlsx"]):
                    yield response.follow(
                        urljoin(response.url, href),
                        callback=self.handle_file
                    )
                elif any(href.lower().endswith(ext) for ext in [".jpg", ".png", ".js", ".css"]):
                    continue
                elif href.startswith("/") or response.url in href:
                    yield response.follow(
                        urljoin(response.url, href),
                        callback=self.parse
                    )

    def handle_file(self, response):
        file_ext = os.path.splitext(response.url)[1].lower()
        filename = os.path.basename(response.url)
        filename = "".join(c if c.isalnum() or c in ('.', '_') else '_' for c in filename)
        file_path = os.path.join(self.download_dir, filename)
        
        with open(file_path, 'wb') as f:
            f.write(response.body)
        
        yield {
            "url": response.url,
            "type": "file",
            "file_type": file_ext[1:],
            "file_path": file_path,
            "timestamp": datetime.utcnow().isoformat()
        }

def run_spider(username, user_id):
    """Run the scraper and save output to JSON."""
    output_file = f"/app/data/{username}_{user_id}/combined_output.json"
    process = CrawlerProcess(settings={
        'FEEDS': {
            output_file: {
                'format': 'json',
                'encoding': 'utf8',
                'store_empty': False,
                'indent': 4,
            },
        },
        'USER_AGENT': 'Mozilla/5.0',
    })
    process.crawl(SiteSpider, username=username, user_id=user_id)
    process.start()
    return output_file

# import scrapy
# from scrapy.crawler import CrawlerProcess
# from urllib.parse import urljoin
# import os
# from pathlib import Path
# from datetime import datetime
# import logging
# from .models import Answer

# class SiteSpider(scrapy.Spider):
#     name = "site"
#     download_dir = "/app/data"  # Docker volume path
#     custom_settings = {
#         'LOG_LEVEL': 'INFO',
#         'HTTPCACHE_ENABLED': True,
#         'CONCURRENT_REQUESTS': 4,  # Reduce concurrency to save memory
#         'MEMUSAGE_LIMIT_MB': 256,  # Set memory limit
#     }

#     def __init__(self, username, user_id, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.username = username
#         self.user_id = user_id
#         self.download_dir = os.path.join(self.download_dir, f"{username}_{user_id}", "downloads")
#         if not os.path.exists(self.download_dir):
#             os.makedirs(self.download_dir)
        
#         try:
#             answers = Answer.objects.filter(user=self.user_id)
#             self.answer_text = str(answers[0].response) if answers.exists() else ""
#             self.start_urls = [self.answer_text] if self.answer_text else []
#         except Exception as e:
#             logging.error(f"Error initializing spider: {e}")
#             self.start_urls = []

#     def parse(self, response):
#         try:
#             content_type = response.headers.get("Content-Type", b"").decode().lower()
            
#             if "text/html" in content_type:
#                 text = response.xpath("//body//text()").getall()
#                 clean_text = " ".join(t.strip() for t in text if t.strip())
#                 yield {
#                     "url": response.url,
#                     "text": clean_text,
#                     "type": "html",
#                     "timestamp": datetime.utcnow().isoformat()
#                 }

#                 for href in response.css("a::attr(href)").getall():
#                     try:
#                         if any(href.lower().endswith(ext) for ext in [".pdf", ".doc", ".docx", ".xls", ".xlsx"]):
#                             yield response.follow(
#                                 urljoin(response.url, href),
#                                 callback=self.handle_file
#                             )
#                         elif any(href.lower().endswith(ext) for ext in [".jpg", ".png", ".js", ".css"]):
#                             continue
#                         elif href.startswith("/") or response.url in href:
#                             yield response.follow(
#                                 urljoin(response.url, href),
#                                 callback=self.parse
#                             )
#                     except Exception as e:
#                         logging.error(f"Error processing link {href}: {e}")

#         except Exception as e:
#             logging.error(f"Error parsing {response.url}: {e}")

#     def handle_file(self, response):
#         try:
#             file_ext = os.path.splitext(response.url)[1].lower()
#             filename = os.path.basename(response.url)
#             filename = "".join(c if c.isalnum() or c in ('.', '_') else '_' for c in filename)
#             file_path = os.path.join(self.download_dir, filename)
            
#             with open(file_path, 'wb') as f:
#                 f.write(response.body)
            
#             yield {
#                 "url": response.url,
#                 "type": "file",
#                 "file_type": file_ext[1:],
#                 "file_path": file_path,
#                 "timestamp": datetime.utcnow().isoformat()
#             }
#         except Exception as e:
#             logging.error(f"Error handling file {response.url}: {e}")

# def run_spider(username, user_id):
#     """Run the scraper and save output to JSON."""
#     try:
#         output_dir = f"/app/data/{username}_{user_id}"
#         if not os.path.exists(output_dir):
#             os.makedirs(output_dir)
            
#         output_file = os.path.join(output_dir, "combined_output.json")
        
#         process = CrawlerProcess(settings={
#             'FEEDS': {
#                 output_file: {
#                     'format': 'json',
#                     'encoding': 'utf8',
#                     'store_empty': False,
#                     'indent': 4,
#                 },
#             },
#             'USER_AGENT': 'Mozilla/5.0',
#             'LOG_LEVEL': 'INFO',
#             'MEMUSAGE_LIMIT_MB': 256,
#             'HTTPCACHE_ENABLED': True,
#         })
#         process.crawl(SiteSpider, username=username, user_id=user_id)
#         process.start()
#         return output_file
#     except Exception as e:
#         logging.error(f"Error running spider: {e}")
#         return None