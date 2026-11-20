"""
H.Huddair's Nexus-Pulse - Level 1
Agent Module: Localization Engine for Non-English & Multi-Region Search Queries
Translates industry niches into native, idiomatically authentic B2B search queries
for Germany, France, Russia, Spain, Italy, Middle East, and more.
"""

from typing import Dict, List, Any


# Localized terminology dictionaries
LOCALIZATION_MATRIX: Dict[str, Dict[str, Any]] = {
    "germany": {
        "lang_code": "de",
        "tld": ".de",
        "niche_translations": {
            "commercial construction": "Gewerblicher Hochbau Bauunternehmen",
            "general contractors": "Generalunternehmer Hochbau",
            "mep engineering": "TGA Technische Gebäudeausrüstung",
            "commercial roofing": "Industriedachbau Dachdeckerbetrieb",
            "civil infrastructure": "Tiefbau Ingenieurbau",
            "architecture": "Architekturbüro Generalplanung"
        },
        "intent_triggers": [
            "Ausschreibungen",
            "Kalkulation",
            "Bauangebot",
            "Leistungsverzeichnis",
            "Einkauf Nachunternehmer",
            "Projektentwicklung"
        ],
        "contact_anchors": ["Impressum", "Kontakt", "Ansprechpartner", "Standort"]
    },
    "france": {
        "lang_code": "fr",
        "tld": ".fr",
        "niche_translations": {
            "commercial construction": "Bâtiment travaux publics commercial",
            "general contractors": "Entreprise générale de bâtiment",
            "mep engineering": "Génie climatique et électrique CVC",
            "commercial roofing": "Étanchéité et toiture industrielle",
            "civil infrastructure": "Travaux publics génie civil",
            "architecture": "Cabinet d'architecture maîtrise d'œuvre"
        },
        "intent_triggers": [
            "Appels d'offres",
            "Bureau d'études chiffrage",
            "Devis estimatif",
            "Métré et études de prix",
            "Consultation sous-traitants"
        ],
        "contact_anchors": ["Mentions légales", "Contact", "Direction", "Siège social"]
    },
    "russia": {
        "lang_code": "ru",
        "tld": ".ru",
        "niche_translations": {
            "commercial construction": "Строительство коммерческой недвижимости",
            "general contractors": "Генеральный подрядчик строительные работы",
            "mep engineering": "Инженерные системы вентиляция отопление ОВиК",
            "commercial roofing": "Кровельные работы промышленные объекты",
            "civil infrastructure": "Инфраструктурное строительство нулевой цикл",
            "architecture": "Проектное бюро архитектурное проектирование"
        },
        "intent_triggers": [
            "Тендерный отдел",
            "Сметный отдел",
            "Расчет сметы стоимости",
            "Участие в тендерах",
            "Отдел закупок снабжения"
        ],
        "contact_anchors": ["Контакты", "Реквизиты", "Отдел продаж", "Руководство"]
    },
    "spain": {
        "lang_code": "es",
        "tld": ".es",
        "niche_translations": {
            "commercial construction": "Construcción edificación no residencial",
            "general contractors": "Empresas constructoras contratistas generales",
            "mep engineering": "Instalaciones climatización fontanería electricidad",
            "commercial roofing": "Cubiertas y naves industriales",
            "civil infrastructure": "Obra civil y urbanismo",
            "architecture": "Estudio de arquitectura y urbanismo"
        },
        "intent_triggers": [
            "Licitaciones de obra",
            "Departamento de estudios y presupuestos",
            "Jefe de compras contratación",
            "Concurso de proyectos"
        ],
        "contact_anchors": ["Aviso legal", "Contacto", "Dónde estamos", "Equipo directivo"]
    },
    "italy": {
        "lang_code": "it",
        "tld": ".it",
        "niche_translations": {
            "commercial construction": "Costruzioni commerciali edili industriali",
            "general contractors": "General contractor imprese edili",
            "mep engineering": "Impianti tecnologici termoidraulici",
            "commercial roofing": "Coperture industriali impermeabilizzazioni",
            "civil infrastructure": "Opere civili infrastrutturali",
            "architecture": "Studio di architettura e progettazione"
        },
        "intent_triggers": [
            "Gare d'appalto",
            "Ufficio preventivi computo metrico",
            "Ufficio acquisti fornitori",
            "Bando di gara"
        ],
        "contact_anchors": ["Contatti", "Chi siamo", "Note legali", "Sede legale"]
    },
    "united kingdom": {
        "lang_code": "en",
        "tld": ".co.uk",
        "niche_translations": {
            "commercial construction": "Commercial Building Construction",
            "general contractors": "Main Contractors Commercial Fitout",
            "mep engineering": "Building Services M&E Contractors",
            "commercial roofing": "Industrial Roofing & Cladding Contractors",
            "civil infrastructure": "Civil Engineering & Groundworks",
            "architecture": "Chartered Architectural Practice"
        },
        "intent_triggers": [
            "Estimating Department",
            "Tenders and Bids",
            "Quantity Surveying",
            "Procurement Portal",
            "Subcontractor Enquiries"
        ],
        "contact_anchors": ["Contact Us", "Estimating", "Head Office", "About Us"]
    },
    "united states": {
        "lang_code": "en",
        "tld": ".com",
        "niche_translations": {
            "commercial construction": "Commercial General Contracting",
            "general contractors": "Commercial General Contractors",
            "mep engineering": "Mechanical Electrical Plumbing MEP",
            "commercial roofing": "Commercial Roofing Contractors",
            "civil infrastructure": "Heavy Civil & Infrastructure",
            "architecture": "Commercial Architectural Firm"
        },
        "intent_triggers": [
            "Estimating Department",
            "Bid Room",
            "Plan Room",
            "Subcontractor Pre-qualification",
            "RFP Submissions"
        ],
        "contact_anchors": ["Contact Us", "Locations", "Leadership", "Estimating"]
    },
    "united arab emirates": {
        "lang_code": "en",
        "tld": ".ae",
        "niche_translations": {
            "commercial construction": "Commercial Building Construction",
            "general contractors": "General Contracting Companies",
            "luxury real estate": "Luxury Real Estate Properties Agencies",
            "architecture": "Architectural Consulting Engineering",
            "mep engineering": "MEP Contracting Services"
        },
        "intent_triggers": [
            "Commercial Department",
            "Procurement",
            "Business Inquiries",
            "Tenders",
            "Client Relations"
        ],
        "contact_anchors": ["Contact Us", "Head Office", "About Us", "Inquiries"]
    },
    "saudi arabia": {
        "lang_code": "ar",
        "tld": ".sa",
        "niche_translations": {
            "commercial construction": "شركات المقاولات والإنشاءات",
            "general contractors": "المقاولون العموميون",
            "luxury real estate": "العقارات الفاخرة والاستثمار العقاري"
        },
        "intent_triggers": [
            "إدارة المشتريات",
            "المناقصات والعقود",
            "التواصل التجاري"
        ],
        "contact_anchors": ["اتصل بنا", "تواصل معنا", "من نحن", "المكتب الرئيسي"]
    },
    "canada": {
        "lang_code": "en",
        "tld": ".ca",
        "niche_translations": {
            "commercial construction": "Commercial General Contractors",
            "general contractors": "General Contracting Construction"
        },
        "intent_triggers": ["Estimating", "Tenders", "Procurement", "Inquiries"],
        "contact_anchors": ["Contact Us", "Head Office", "About Us"]
    },
    "australia": {
        "lang_code": "en",
        "tld": ".com.au",
        "niche_translations": {
            "commercial construction": "Commercial Building Contractors",
            "general contractors": "Commercial Head Contractors"
        },
        "intent_triggers": ["Tenders", "Estimating", "Commercial Enquiries"],
        "contact_anchors": ["Contact Us", "Head Office", "About Us"]
    },
    "netherlands": {
        "lang_code": "nl",
        "tld": ".nl",
        "niche_translations": {
            "commercial construction": "Commerciële Utiliteitsbouw Bouwbedrijf",
            "general contractors": "Hoofdaannemer Bouw"
        },
        "intent_triggers": ["Aanbestedingen", "Calculatie", "Inkoop"],
        "contact_anchors": ["Contact", "Over ons", "Vestiging"]
    },
    "switzerland": {
        "lang_code": "de",
        "tld": ".ch",
        "niche_translations": {
            "commercial construction": "Gewerbebau Generalunternehmung",
            "general contractors": "Generalunternehmer Bau"
        },
        "intent_triggers": ["Ausschreibungen", "Kalkulation", "Bauofferten"],
        "contact_anchors": ["Kontakt", "Impressum", "Standort"]
    },
    "austria": {
        "lang_code": "de",
        "tld": ".at",
        "niche_translations": {
            "commercial construction": "Gewerblicher Hochbau Bauunternehmen",
            "general contractors": "Generalunternehmer Hochbau"
        },
        "intent_triggers": ["Ausschreibungen", "Kalkulation", "Angebote"],
        "contact_anchors": ["Kontakt", "Impressum", "Standort"]
    }
}


class LocalizationEngine:
    """
    Translates and expands target country/city/niche criteria into high-conversion
    native B2B search strings for automated discovery.
    """

    @staticmethod
    def get_supported_countries() -> List[str]:
        return list(LOCALIZATION_MATRIX.keys())

    @staticmethod
    def generate_localized_queries(
        country: str,
        city: str,
        niche: str,
        max_queries: int = 5
    ) -> List[Dict[str, str]]:
        """
        Generates authentic search queries using native idioms, localized syntax,
        and commercial intent operators.
        """
        clean_country = country.strip().lower()
        clean_city = city.strip()
        clean_niche = niche.strip().lower()

        # Normalise short aliases used by the UI's GEO_REGIONS dropdown
        _COUNTRY_ALIASES = {
            "uk": "united kingdom",
            "usa": "united states",
            "us": "united states",
            "uae": "united arab emirates",
            "ksa": "saudi arabia",
        }
        clean_country = _COUNTRY_ALIASES.get(clean_country, clean_country)

        # Find matching locale or fallback to English
        locale = LOCALIZATION_MATRIX.get(clean_country)
        if not locale:
            # Fuzzy match
            for c_name, c_data in LOCALIZATION_MATRIX.items():
                if c_name in clean_country or clean_country in c_name:
                    locale = c_data
                    break
        if not locale:
            locale = LOCALIZATION_MATRIX["united states"]

        lang_code = locale["lang_code"]
        tld = locale["tld"]

        # Resolve localized niche
        localized_niche = ""
        for n_key, n_trans in locale["niche_translations"].items():
            if n_key in clean_niche or clean_niche in n_key:
                localized_niche = n_trans
                break
        if not localized_niche:
            localized_niche = niche

        intents = locale["intent_triggers"]
        anchors = locale["contact_anchors"]

        # Check whether this is a construction/contractor-focused niche
        construction_keywords = (
            "construction", "contractor", "hochbau", "tiefbau", "bâtiment",
            "building", "roofing", "mep", "tga", "civil", "infrastructure",
            "architecture", "architect", "engineering", "plumbing", "electrical",
            "bauunternehmen", "travaux", "edificación"
        )
        is_construction = any(ck in clean_niche for ck in construction_keywords)

        queries: List[Dict[str, str]] = []

        if is_construction:
            # Construction-specific bidding/tender/estimating operators
            q1 = f'"{localized_niche}" "{clean_city}" ("{intents[0]}" OR "{intents[1]}") site:{tld}'
            queries.append({
                "type": "HIGH_INTENT_ESTIMATING",
                "query": q1,
                "language": lang_code,
                "description": f"Targeting estimating & bidding departments in {city}"
            })

            q2 = f'"{localized_niche}" "{clean_city}" "{anchors[0]}" "{anchors[1]}" email'
            queries.append({
                "type": "DIRECT_CONTACT_DISCOVERY",
                "query": q2,
                "language": lang_code,
                "description": f"Targeting corporate contact & directory pages in {city}"
            })

            trigger_3 = intents[2] if len(intents) > 2 else intents[0]
            q3 = f'"{localized_niche}" "{clean_city}" "{trigger_3}" ("@")'
            queries.append({
                "type": "PROCUREMENT_PORTAL",
                "query": q3,
                "language": lang_code,
                "description": f"Targeting procurement and tender submissions in {city}"
            })

            anchor_lead = anchors[2] if len(anchors) > 2 else anchors[0]
            q4 = f'"{localized_niche}" "{clean_city}" "{anchor_lead}" ("mailto:")'
            queries.append({
                "type": "LEADERSHIP_MAILTO",
                "query": q4,
                "language": lang_code,
                "description": f"Targeting mailto links on {city} contractor sites"
            })
        else:
            # Universal Multi-Niche Commercial queries (Luxury Real Estate, SaaS, Fitness, etc.)
            q1 = f'"{localized_niche}" "{clean_city}" contact email site:{tld}'
            queries.append({
                "type": "NICHE_LOCAL_CONTACT",
                "query": q1,
                "language": lang_code,
                "description": f"Targeting verified {niche} contact pages in {city}"
            })

            q2 = f'"{localized_niche}" ("agency" OR "company" OR "firm" OR "brokerage" OR "office") "{clean_city}" email'
            queries.append({
                "type": "NICHE_COMMERCIAL_FIRM",
                "query": q2,
                "language": lang_code,
                "description": f"Targeting corporate {niche} companies in {city}"
            })

            q3 = f'"{localized_niche}" "{clean_city}" ("contact us" OR "inquiries" OR "office") email'
            queries.append({
                "type": "NICHE_INQUIRIES",
                "query": q3,
                "language": lang_code,
                "description": f"Targeting commercial inquiries for {niche} in {city}"
            })

            q4 = f'"{localized_niche}" "{clean_city}" "{country}" "info@" OR "contact@"'
            queries.append({
                "type": "NICHE_DIRECT_MAIL",
                "query": q4,
                "language": lang_code,
                "description": f"Targeting direct mail contacts for {niche} in {city}"
            })

            q5 = f'"{localized_niche}" in "{clean_city}" official website contact'
            queries.append({
                "type": "NICHE_OFFICIAL_WEBSITE",
                "query": q5,
                "language": lang_code,
                "description": f"Targeting official websites for {niche} in {city}"
            })

        return queries[:max_queries]


if __name__ == "__main__":
    loc = LocalizationEngine()
    print("GERMANY:")
    for q in loc.generate_localized_queries("Germany", "Berlin", "Commercial Construction"):
        print(f" -> [{q['type']}] {q['query']}")

    print("\nRUSSIA:")
    for q in loc.generate_localized_queries("Russia", "Moscow", "General Contractors"):
        print(f" -> [{q['type']}] {q['query']}")

    print("\nFRANCE:")
    for q in loc.generate_localized_queries("France", "Paris", "Commercial Construction"):
        print(f" -> [{q['type']}] {q['query']}")
