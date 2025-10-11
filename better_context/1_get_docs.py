import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeepCrawlStrategy, LXMLWebScrapingStrategy, URLPatternFilter, DomainFilter, FilterChain, CacheMode
import json

async def main():
    results_md = {}

    domain_filter = DomainFilter(allowed_domains=["docs.weaviate.io"])
    config = CrawlerRunConfig(
            deep_crawl_strategy=BFSDeepCrawlStrategy(
                max_depth=4,
                include_external=False,
                filter_chain=FilterChain([domain_filter]),
            ),
            scraping_strategy=LXMLWebScrapingStrategy(),
            verbose=True,
            cache_mode=CacheMode.ENABLED
        )
    async with AsyncWebCrawler() as crawler:
        results = await crawler.arun("https://docs.weaviate.io/weaviate", config=config)

        print(f"Crawled {len(results)} pages in total")

        # Write results to file
        for result in results:
            results_md[result.url] = result.markdown

    with open("./output/weaviate_docs_crawl4ai.json", "w") as f:
        json.dump(results_md, f)

if __name__ == "__main__":
    asyncio.run(main())
