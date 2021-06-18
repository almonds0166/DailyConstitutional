
from typing import Optional
import asyncio
from http.client import responses as RESPONSE_CODES
import re

import aiohttp
import async_timeout
import feedparser
from bs4 import BeautifulSoup
import html5lib # pour que pipreqs voir
from markdownify import markdownify

IDIOM_OF_THE_DAY = "https://www.englishclub.com/ref/idiom-of-the-day.xml"
TIMEOUT = 10 # s
HEADERS = {
   "User-Agent": "Kotobot/2.0",
}

class Idiom:
   """Représenter une idiome.

   Keyword Args:
      title: L'idiome lui-même.
      url: Une URL vers l'idiome (EnglishClub).
      meaning: Le sens ou le résumé de l'idiome.
      example: Le ou les exemples de l'idiome.

   Attributes:
      title: L'idiome lui-même.
      url: Une URL vers l'idiome (EnglishClub).
      meaning: Le sens ou le résumé de l'idiome.
      example: Le ou les exemples de l'idiome.
   """
   def __init__(self, *,
      title: str,
      url: Optional[str]=None,
      meaning: str="",
      example: str=""
   ):
      self.title = title
      self.url = url
      self.meaning = meaning
      self.example = example

   @staticmethod
   async def fetch_idiom_of_the_day():
      """Récupérer l'idiome du jour du serveur.

      Throws:
         RuntimeError: Pour une session expirée (10 s) ou une erreur HTTP.

      Returns:
         idiom (Idiom): L'idiome du jour.
      """
      async with aiohttp.ClientSession(trace_configs=None, headers=HEADERS) as session:
         with async_timeout.timeout(TIMEOUT) as at:
            async with session.get(IDIOM_OF_THE_DAY) as response:
               if response.status == 200:
                  html = await response.text()
               else:
                  raise RuntimeError(
                     f"Oh non ! Le code HTTP : " \
                     f"{response.status} {RESPONSE_CODES[response.status]}"
                  )
         if at.expired:
            raise RuntimeError("Session expirée")

         await asyncio.sleep(1)

         rss = feedparser.parse(html)
         entry = rss["entries"][0]

         url = entry["link"]
         summary = entry["summary"]
         title = entry["title"]

         idiom = Idiom(
            title=title,
            url=url,
            meaning=summary
         )

         # Récupérer les exemples
         with async_timeout.timeout(TIMEOUT) as at:
            async with session.get(url) as response:
               if response.status == 200:
                  html = await response.text()
               else:
                  raise RuntimeError(
                     f"Oh non ! Le code HTTP : " \
                     f"{response.status} {RESPONSE_CODES[response.status]}"
                  )
         if at.expired:
            raise RuntimeError("Session expirée")

         soup = BeautifulSoup(html, "html5lib")

         div = soup.body.find_all("div", class_="example")[0]
         div.h2.decompose()
         md = markdownify(str(div))
         md = re.sub(r"[ \t]+", " ", md)
         md = re.sub(r"\n+", "\n", md)

         idiom.example = md.strip()

         return idiom

async def main():
   idiom = await Idiom.fetch_idiom_of_the_day()
   print(idiom.title)
   print(idiom.url)
   print(idiom.meaning)
   print(idiom.example)

if __name__ == "__main__":
   loop = asyncio.get_event_loop()
   loop.run_until_complete(main())