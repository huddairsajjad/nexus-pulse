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

        queries: List[Dict[str, str]] = []

        # Query 1: High-precision intent (Estimating / Tenders / Bids in native language)
        q1 = f'"{localized_niche}" "{clean_city}" ("{intents[0]}" OR "{intents[1]}") site:{tld}'
        queries.append({
            "type": "HIGH_INTENT_ESTIMATING",
            "query": q1,
            "language": lang_code,
            "description": f"Targeting estimating & bidding departments in {city}"
        })

        # Query 2: Direct contact & imprint discovery
        q2 = f'"{localized_niche}" "{clean_city}" "{anchors[0]}" "{anchors[1]}" email'
        queries.append({
            "type": "DIRECT_CONTACT_DISCOVERY",
            "query": q2,
            "language": lang_code,
            "description": f"Targeting corporate contact & directory pages in {city}"
        })

        # Query 3: Subcontractor & Procurement portal
        trigger_3 = intents[2] if len(intents) > 2 else intents[0]
        q3 = f'"{localized_niche}" "{clean_city}" "{trigger_3}" ("@")'
        queries.append({
            "type": "PROCUREMENT_PORTAL",
            "query": q3,
            "language": lang_code,
            "description": f"Targeting procurement and tender submissions in {city}"
        })

        # Query 4: Executive leadership and commercial directory
        anchor_lead = anchors[2] if len(anchors) > 2 else anchors[0]
        q4 = f'"{localized_niche}" "{clean_city}" "{anchor_lead}" ("mailto:")'
        queries.append({
            "type": "LEADERSHIP_MAILTO",
            "query": q4,
            "language": lang_code,
            "description": f"Targeting mailto links on {city} contractor sites"
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
