"""
Wikimedia Commons API Scraper - Geliştirilmiş Versiyon
Daha fazla görsel için optimize edildi
"""
import aiohttp
import asyncio
from typing import List, Dict, Optional, Any
from urllib.parse import quote
import re


class WikimediaScraper:
    """Wikimedia Commons API üzerinden WW2 görselleri arama ve indirme"""
    
    BASE_URL = "https://commons.wikimedia.org/w/api.php"
    
    # WW2 ile ilgili Wikimedia kategorileri - GENİŞLETİLMİŞ
    WW2_CATEGORIES = {
        "tanklar": [
            "World War II tanks",
            "Tanks of World War II",
            "German tanks of World War II",
            "American tanks of World War II",
            "Soviet tanks of World War II",
            "British tanks of World War II",
            "Panzer IV",
            "Panzer III",
            "Panzer V Panther",
            "Tiger I",
            "Tiger II",
            "Sherman tank",
            "M4 Sherman",
            "T-34",
            "KV-1",
            "IS-2",
            "Churchill tank",
            "Cromwell tank",
            "Tank destroyers of World War II",
            "Armored cars of World War II"
        ],
        "ucaklar": [
            "World War II aircraft",
            "Fighter aircraft of World War II",
            "Bombers of World War II",
            "Luftwaffe aircraft",
            "Royal Air Force aircraft of World War II",
            "United States Army Air Forces aircraft",
            "Soviet Air Force aircraft of World War II",
            "Supermarine Spitfire",
            "Messerschmitt Bf 109",
            "Focke-Wulf Fw 190",
            "P-51 Mustang",
            "P-47 Thunderbolt",
            "B-17 Flying Fortress",
            "B-24 Liberator",
            "B-29 Superfortress",
            "Junkers Ju 87",
            "Heinkel He 111",
            "Mitsubishi A6M Zero",
            "Hawker Hurricane",
            "Lancaster bomber"
        ],
        "gemiler": [
            "World War II naval ships",
            "Battleships of World War II",
            "Aircraft carriers of World War II",
            "Submarines of World War II",
            "Destroyers of World War II",
            "Cruisers of World War II",
            "U-boats",
            "Type VII submarines",
            "Type XXI submarines",
            "USS Missouri (BB-63)",
            "USS Enterprise (CV-6)",
            "Bismarck (ship, 1939)",
            "Tirpitz (ship)",
            "Yamato (ship)",
            "HMS Hood",
            "PT boats",
            "Liberty ships"
        ],
        "askerler": [
            "Soldiers of World War II",
            "German soldiers of World War II",
            "American soldiers of World War II",
            "Soviet soldiers of World War II",
            "British soldiers of World War II",
            "Military personnel of World War II",
            "Paratroopers of World War II",
            "Marines in World War II",
            "Wehrmacht soldiers",
            "Red Army soldiers",
            "US Army soldiers in World War II",
            "Waffen-SS personnel",
            "RAF personnel of World War II",
            "Resistance fighters of World War II",
            "Prisoners of war in World War II"
        ],
        "haritalar": [
            "Maps of World War II",
            "Military maps of World War II",
            "World War II in Europe maps",
            "World War II in the Pacific maps",
            "D-Day maps",
            "Eastern Front maps",
            "Western Front (World War II) maps",
            "Battle maps",
            "Strategic maps of World War II",
            "Operation Barbarossa maps",
            "Operation Overlord maps",
            "Maps of the Holocaust"
        ],
        "savas_sahneleri": [
            "Battles of World War II",
            "World War II combat",
            "D-Day",
            "Normandy landings",
            "Battle of Stalingrad",
            "Battle of Berlin",
            "Battle of Midway",
            "Pearl Harbor attack",
            "Battle of the Bulge",
            "Battle of Kursk",
            "Battle of Britain",
            "Battle of El Alamein",
            "Battle of Iwo Jima",
            "Battle of Okinawa",
            "Operation Market Garden",
            "Operation Barbarossa",
            "Siege of Leningrad",
            "Fall of Berlin"
        ],
        "posterler": [
            "World War II posters",
            "American World War II posters",
            "German World War II posters",
            "British World War II posters",
            "Soviet World War II posters",
            "Propaganda posters of World War II",
            "Recruitment posters of World War II",
            "War bond posters",
            "Nazi propaganda",
            "Allied propaganda of World War II",
            "Home front posters"
        ],
        "liderler": [
            "World War II leaders",
            "Generals of World War II",
            "World War II military personnel",
            "Winston Churchill",
            "Franklin D. Roosevelt",
            "Dwight D. Eisenhower",
            "Bernard Montgomery",
            "George S. Patton",
            "Douglas MacArthur",
            "Erwin Rommel",
            "Georgy Zhukov",
            "Charles de Gaulle",
            "Omar Bradley",
            "Chester Nimitz",
            "Heinz Guderian",
            "Erich von Manstein"
        ]
    }
    
    # Türkçe-İngilizce arama terimleri - GENİŞLETİLMİŞ
    SEARCH_TERMS = {
        "tanklar": [
            "ww2 tank", "world war 2 tank", "panzer", "sherman tank", "t-34 tank", 
            "tiger tank", "panther tank", "armored vehicle ww2", "tank battle",
            "tank destroyer", "panzerkampfwagen", "m4 sherman", "churchill tank"
        ],
        "ucaklar": [
            "ww2 aircraft", "world war 2 plane", "fighter plane ww2", "bomber ww2",
            "luftwaffe", "spitfire", "messerschmitt", "p-51 mustang", "b-17",
            "zero fighter", "hurricane fighter", "focke wulf", "junkers", "heinkel"
        ],
        "gemiler": [
            "ww2 ship", "battleship ww2", "warship world war 2", "submarine ww2",
            "u-boat", "aircraft carrier ww2", "destroyer ww2", "navy ww2",
            "bismarck ship", "yamato ship", "uss missouri", "pt boat"
        ],
        "askerler": [
            "ww2 soldier", "world war 2 troops", "infantry ww2", "army ww2",
            "wehrmacht soldier", "gi soldier", "red army soldier", "paratrooper ww2",
            "marine ww2", "commando ww2", "resistance fighter"
        ],
        "haritalar": [
            "ww2 map", "world war 2 map", "battle map ww2", "military map ww2",
            "war map", "front line map", "d-day map", "operation map ww2",
            "strategy map world war", "europe 1944 map"
        ],
        "savas_sahneleri": [
            "ww2 battle", "world war 2 combat", "war scene ww2", "fighting ww2",
            "d-day", "normandy landing", "stalingrad", "berlin 1945",
            "pearl harbor", "iwo jima", "okinawa battle", "blitzkrieg"
        ],
        "posterler": [
            "ww2 poster", "world war 2 propaganda", "war poster", "recruitment poster",
            "propaganda ww2", "war bond poster", "nazi poster", "allied poster",
            "home front poster", "victory poster"
        ],
        "liderler": [
            "ww2 general", "world war 2 commander", "military leader ww2",
            "allied leader ww2", "eisenhower", "patton", "montgomery",
            "rommel", "macarthur", "zhukov", "churchill ww2"
        ]
    }
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.rate_limit_delay = 0.3  # Daha hızlı API çağrıları
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """HTTP session oluştur veya mevcut olanı döndür"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                headers={
                    "User-Agent": "WW2ImageArchive/1.0 (Educational Project)"
                }
            )
        return self.session
    
    async def close(self):
        """Session'ı kapat"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def search_images(
        self, 
        query: str, 
        category_slug: Optional[str] = None,
        limit: int = 100,  # Artırıldı
        offset: int = 0,
        min_width: int = 600  # Düşürüldü - daha fazla sonuç
    ) -> Dict[str, Any]:
        """
        Görsel arama - Geliştirilmiş versiyon
        Birden fazla arama terimi ile arama yapar
        """
        session = await self._get_session()
        all_images = []
        seen_ids = set()
        
        # Arama sorgularını hazırla
        search_queries = [f"World War II {query}", f"WW2 {query}", f"WWII {query}"]
        
        # Kategori bazlı ek terimler ekle
        if category_slug and category_slug in self.SEARCH_TERMS:
            extra_terms = self.SEARCH_TERMS[category_slug][:5]  # İlk 5 terimi kullan
            for term in extra_terms:
                search_queries.append(f"{query} {term}")
        
        # Her sorgu için arama yap
        for search_query in search_queries[:6]:  # Maksimum 6 sorgu
            if len(all_images) >= limit:
                break
                
            params = {
                "action": "query",
                "format": "json",
                "generator": "search",
                "gsrsearch": f"filetype:bitmap {search_query}",
                "gsrlimit": min(50, limit - len(all_images)),
                "gsroffset": offset,
                "gsrnamespace": 6,
                "prop": "imageinfo",
                "iiprop": "url|size|mime|extmetadata",
                "iiurlwidth": 400,
            }
            
            try:
                async with session.get(self.BASE_URL, params=params) as response:
                    if response.status != 200:
                        continue
                    
                    data = await response.json()
                    
                    if "query" not in data or "pages" not in data["query"]:
                        continue
                    
                    for page_id, page_data in data["query"]["pages"].items():
                        if page_id in seen_ids:
                            continue
                        seen_ids.add(page_id)
                        
                        if "imageinfo" not in page_data:
                            continue
                        
                        info = page_data["imageinfo"][0]
                        
                        width = info.get("width", 0)
                        if width < min_width:
                            continue
                        
                        mime = info.get("mime", "")
                        if not mime.startswith("image/"):
                            continue
                        
                        extmeta = info.get("extmetadata", {})
                        
                        image = {
                            "source_id": str(page_id),
                            "title": self._clean_title(page_data.get("title", "")),
                            "description": self._get_meta_value(extmeta, "ImageDescription"),
                            "source_url": info.get("url", ""),
                            "thumbnail_url": info.get("thumburl", info.get("url", "")),
                            "width": width,
                            "height": info.get("height", 0),
                            "file_size": info.get("size", 0),
                            "mime_type": mime,
                            "license": self._get_meta_value(extmeta, "LicenseShortName"),
                            "author": self._get_meta_value(extmeta, "Artist"),
                            "source": "wikimedia"
                        }
                        all_images.append(image)
                
                await asyncio.sleep(self.rate_limit_delay)
                
            except Exception as e:
                print(f"Arama hatası ({search_query}): {e}")
                continue
        
        return {
            "success": True,
            "images": all_images[:limit],
            "total": len(all_images),
            "query": query
        }
    
    async def get_category_images(
        self,
        category_slug: str,
        limit: int = 100,  # Artırıldı
        continue_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Wikimedia kategorisinden görseller getir - Geliştirilmiş versiyon
        Daha fazla kategori tarar
        """
        if category_slug not in self.WW2_CATEGORIES:
            return {"success": False, "error": "Kategori bulunamadı", "images": []}
        
        session = await self._get_session()
        all_images = []
        seen_ids = set()
        
        # Kategorideki TÜM alt kategorileri kullan (önceden sadece 3 idi)
        categories = self.WW2_CATEGORIES[category_slug][:10]  # İlk 10 kategori
        
        for wiki_category in categories:
            if len(all_images) >= limit:
                break
                
            params = {
                "action": "query",
                "format": "json",
                "generator": "categorymembers",
                "gcmtitle": f"Category:{wiki_category}",
                "gcmtype": "file",
                "gcmlimit": 50,  # Her kategoriden 50 görsel
                "prop": "imageinfo",
                "iiprop": "url|size|mime|extmetadata",
                "iiurlwidth": 400,
            }
            
            if continue_token:
                params["gcmcontinue"] = continue_token
            
            try:
                async with session.get(self.BASE_URL, params=params) as response:
                    if response.status != 200:
                        continue
                    
                    data = await response.json()
                    
                    if "query" not in data or "pages" not in data["query"]:
                        continue
                    
                    for page_id, page_data in data["query"]["pages"].items():
                        if page_id in seen_ids:
                            continue
                        seen_ids.add(page_id)
                        
                        if "imageinfo" not in page_data:
                            continue
                        
                        info = page_data["imageinfo"][0]
                        
                        # Minimum genişlik düşürüldü - 600px
                        if info.get("width", 0) < 600:
                            continue
                        
                        mime = info.get("mime", "")
                        if not mime.startswith("image/"):
                            continue
                        
                        extmeta = info.get("extmetadata", {})
                        
                        image = {
                            "source_id": str(page_id),
                            "title": self._clean_title(page_data.get("title", "")),
                            "description": self._get_meta_value(extmeta, "ImageDescription"),
                            "source_url": info.get("url", ""),
                            "thumbnail_url": info.get("thumburl", info.get("url", "")),
                            "width": info.get("width", 0),
                            "height": info.get("height", 0),
                            "file_size": info.get("size", 0),
                            "mime_type": mime,
                            "license": self._get_meta_value(extmeta, "LicenseShortName"),
                            "author": self._get_meta_value(extmeta, "Artist"),
                            "source": "wikimedia"
                        }
                        all_images.append(image)
                
                await asyncio.sleep(self.rate_limit_delay)
                
            except Exception as e:
                print(f"Kategori hatası ({wiki_category}): {e}")
                continue
        
        # Arama ile de görseller ekle
        if len(all_images) < limit and category_slug in self.SEARCH_TERMS:
            search_terms = self.SEARCH_TERMS[category_slug][:3]
            for term in search_terms:
                if len(all_images) >= limit:
                    break
                search_result = await self.search_images(
                    query=term,
                    limit=30,
                    min_width=600
                )
                if search_result["success"]:
                    for img in search_result["images"]:
                        if img["source_id"] not in seen_ids:
                            seen_ids.add(img["source_id"])
                            all_images.append(img)
        
        return {
            "success": True,
            "images": all_images[:limit],
            "total": len(all_images)
        }
    
    async def bulk_search(
        self,
        category_slug: str,
        limit: int = 200
    ) -> Dict[str, Any]:
        """
        Toplu arama - Maksimum görsel bulmak için
        Hem kategori hem de arama terimlerini kullanır
        """
        all_images = []
        seen_ids = set()
        
        # Önce kategori görselleri
        cat_result = await self.get_category_images(category_slug, limit=limit//2)
        if cat_result["success"]:
            for img in cat_result["images"]:
                if img["source_id"] not in seen_ids:
                    seen_ids.add(img["source_id"])
                    all_images.append(img)
        
        # Sonra arama terimleri ile
        if category_slug in self.SEARCH_TERMS:
            for term in self.SEARCH_TERMS[category_slug]:
                if len(all_images) >= limit:
                    break
                search_result = await self.search_images(
                    query=term,
                    limit=30,
                    min_width=600
                )
                if search_result["success"]:
                    for img in search_result["images"]:
                        if img["source_id"] not in seen_ids:
                            seen_ids.add(img["source_id"])
                            all_images.append(img)
        
        return {
            "success": True,
            "images": all_images[:limit],
            "total": len(all_images)
        }
    
    async def download_image(self, url: str) -> Optional[bytes]:
        """Görsel indir"""
        session = await self._get_session()
        
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.read()
                return None
        except Exception as e:
            print(f"İndirme hatası: {e}")
            return None
    
    def _clean_title(self, title: str) -> str:
        """Başlığı temizle"""
        title = re.sub(r'^File:', '', title)
        title = re.sub(r'\.(jpg|jpeg|png|gif|svg|tif|tiff)$', '', title, flags=re.IGNORECASE)
        title = title.replace('_', ' ')
        return title.strip()
    
    def _get_meta_value(self, extmeta: dict, key: str) -> str:
        """Metadata'dan değer al ve HTML taglarını temizle"""
        if key not in extmeta:
            return ""
        
        value = extmeta[key].get("value", "")
        value = re.sub(r'<[^>]+>', '', value)
        return value.strip()[:500]
