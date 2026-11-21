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
    },
    "singapore": {
        "lang_code": "en",
        "tld": ".com.sg",
        "niche_translations": {
            "commercial construction": "Commercial Building Construction Singapore",
            "general contractors": "Main Contractor General Building"
        },
        "intent_triggers": ["Tenders", "BCA Tenders", "Quotations", "Procurement"],
        "contact_anchors": ["Contact Us", "Office", "Enquiry"]
    },
    "japan": {
        "lang_code": "ja",
        "tld": ".co.jp",
        "niche_translations": {
            "commercial construction": "商業建築 建設会社",
            "general contractors": "ゼネコン 総合建設業"
        },
        "intent_triggers": ["入札", "見積もり", "お問い合わせ", "調達"],
        "contact_anchors": ["お問い合わせ", "会社概要", "所在地", "連絡先"]
    },
    "brazil": {
        "lang_code": "pt",
        "tld": ".com.br",
        "niche_translations": {
            "commercial construction": "Construção Civil Comercial Construtora",
            "general contractors": "Empreiteira Construção Civil"
        },
        "intent_triggers": ["Licitações", "Orçamento", "Proposta Comercial", "Cotação"],
        "contact_anchors": ["Contato", "Fale Conosco", "Sobre Nós", "Localização"]
    },
    "mexico": {
        "lang_code": "es",
        "tld": ".com.mx",
        "niche_translations": {
            "commercial construction": "Construcción Comercial Constructora",
            "general contractors": "Contratista General Obras"
        },
        "intent_triggers": ["Licitaciones", "Cotización", "Presupuesto", "Propuestas"],
        "contact_anchors": ["Contacto", "Ubicación", "Sobre Nosotros", "Oficinas"]
    },
    "south africa": {
        "lang_code": "en",
        "tld": ".co.za",
        "niche_translations": {
            "commercial construction": "Commercial Building Construction Contractors",
            "general contractors": "Principal Building Contractors"
        },
        "intent_triggers": ["Tenders", "Estimating", "CIDB Tenders", "RFQs"],
        "contact_anchors": ["Contact Us", "Head Office", "Enquiries"]
    },
    "india": {
        "lang_code": "en",
        "tld": ".co.in",
        "niche_translations": {
            "commercial construction": "Commercial Construction Companies",
            "general contractors": "EPC Civil Contractors"
        },
        "intent_triggers": ["Tenders", "Tender Bids", "Contracts", "Procurement"],
        "contact_anchors": ["Contact Us", "Registered Office", "Corporate Office"]
    },
    "ireland": {
        "lang_code": "en",
        "tld": ".ie",
        "niche_translations": {
            "commercial construction": "Commercial Building Contractors Ireland",
            "general contractors": "Main Building Contractors"
        },
        "intent_triggers": ["Tenders", "Estimating", "eTenders", "Quotations"],
        "contact_anchors": ["Contact Us", "Head Office", "About Us"]
    },
    "sweden": {
        "lang_code": "sv",
        "tld": ".se",
        "niche_translations": {
            "commercial construction": "Kommersiellt Byggföretag Byggentreprenör",
            "general contractors": "Totalentreprenör Bygg"
        },
        "intent_triggers": ["Upphandling", "Kalkyl", "Anbud", "Offert"],
        "contact_anchors": ["Kontakt", "Om oss", "Kontor"]
    },
    "norway": {
        "lang_code": "no",
        "tld": ".no",
        "niche_translations": {
            "commercial construction": "Kommersiell Byggentreprenør Byggefirma",
            "general contractors": "Hovedentreprenør Bygg"
        },
        "intent_triggers": ["Anbud", "Kalkulasjon", "Tilbud", "Innkjøp"],
        "contact_anchors": ["Kontakt oss", "Om oss", "Kontor"]
    },
    "denmark": {
        "lang_code": "da",
        "tld": ".dk",
        "niche_translations": {
            "commercial construction": "Erhvervsbyggeri Byggefirma Entreprenør",
            "general contractors": "Hovedentreprenør Byggeri"
        },
        "intent_triggers": ["Udbud", "Tilbud", "Kalkulation", "Indkøb"],
        "contact_anchors": ["Kontakt", "Om os", "Adresse"]
    },
    "poland": {
        "lang_code": "pl",
        "tld": ".pl",
        "niche_translations": {
            "commercial construction": "Budownictwo Komercyjne Generalny Wykonawca",
            "general contractors": "Generalny Wykonawca Budowlany"
        },
        "intent_triggers": ["Przetargi", "Kosztorysowanie", "Zapytania ofertowe"],
        "contact_anchors": ["Kontakt", "O nas", "Siedziba"]
    },
    "portugal": {
        "lang_code": "pt",
        "tld": ".pt",
        "niche_translations": {
            "commercial construction": "Construção Civil Comercial Empreiteiro",
            "general contractors": "Empreiteiro Geral Construção"
        },
        "intent_triggers": ["Concursos", "Orçamentos", "Propostas", "Contratação"],
        "contact_anchors": ["Contacto", "Sobre nós", "Sede"]
    },
    "belgium": {
        "lang_code": "nl",
        "tld": ".be",
        "niche_translations": {
            "commercial construction": "Utiliteitsbouw Algemene Onderneming",
            "general contractors": "Hoofdaannemer Bouw"
        },
        "intent_triggers": ["Aanbestedingen", "Offertes", "Calculatie"],
        "contact_anchors": ["Contact", "Over ons", "Zetel"]
    },
    "new zealand": {
        "lang_code": "en",
        "tld": ".co.nz",
        "niche_translations": {
            "commercial construction": "Commercial Construction Building Contractors",
            "general contractors": "Commercial Head Contractors"
        },
        "intent_triggers": ["Tenders", "Estimating", "Commercial Tenders"],
        "contact_anchors": ["Contact Us", "Head Office", "About Us"]
    },
    "qatar": {
        "lang_code": "en",
        "tld": ".qa",
        "niche_translations": {
            "commercial construction": "Commercial Construction Contracting Qatar",
            "general contractors": "Main General Contractors"
        },
        "intent_triggers": ["Tenders", "Procurement", "Quotations", "Inquiries"],
        "contact_anchors": ["Contact Us", "Head Office", "Location"]
    },
    "kuwait": {
        "lang_code": "en",
        "tld": ".kw",
        "niche_translations": {
            "commercial construction": "Commercial Contracting Construction Kuwait",
            "general contractors": "General Contracting Companies"
        },
        "intent_triggers": ["Tenders", "Procurement", "Inquiries", "Quotations"],
        "contact_anchors": ["Contact Us", "Office", "About Us"]
    },
    "turkey": {
        "lang_code": "tr",
        "tld": ".com.tr",
        "niche_translations": {
            "commercial construction": "Ticari İnşaat Müteahhitlik Şirketleri",
            "general contractors": "Ana Yüklenici İnşaat"
        },
        "intent_triggers": ["İhale", "Teklif", "Maliyet", "Satınalma"],
        "contact_anchors": ["İletişim", "Hakkımızda", "Merkez Ofis"]
    },
    "egypt": {
        "lang_code": "ar",
        "tld": ".com.eg",
        "niche_translations": {
            "commercial construction": "شركات مقاولات وبناء تجاري",
            "general contractors": "مقاول عام إنشاءات"
        },
        "intent_triggers": ["مناقصات", "عطاءات", "استفسارات", "عروض أسعار"],
        "contact_anchors": ["اتصل بنا", "المركز الرئيسي", "من نحن"]
    },
    "malaysia": {
        "lang_code": "en",
        "tld": ".com.my",
        "niche_translations": {
            "commercial construction": "Commercial Construction Contractors Malaysia",
            "general contractors": "Main Building Contractors"
        },
        "intent_triggers": ["Tenders", "CIDB Tenders", "Procurement", "Quotations"],
        "contact_anchors": ["Contact Us", "Headquarters", "Enquiries"]
    },
    "hong kong": {
        "lang_code": "en",
        "tld": ".hk",
        "niche_translations": {
            "commercial construction": "Commercial Building Construction Contractors",
            "general contractors": "Main Registered General Building Contractors"
        },
        "intent_triggers": ["Tenders", "Quotations", "Procurement", "Estimating"],
        "contact_anchors": ["Contact Us", "Head Office", "Enquiry"]
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
    def resolve_country_profile(country: str) -> Dict[str, Any]:
        """Resolves country string to locale dictionary with fallback for any country."""
        clean_country = country.strip().lower()
        _COUNTRY_ALIASES = {
            "uk": "united kingdom",
            "great britain": "united kingdom",
            "england": "united kingdom",
            "scotland": "united kingdom",
            "wales": "united kingdom",
            "usa": "united states",
            "us": "united states",
            "america": "united states",
            "uae": "united arab emirates",
            "emirates": "united arab emirates",
            "ksa": "saudi arabia",
            "saudi": "saudi arabia",
            "aus": "australia",
            "oz": "australia",
            "nz": "new zealand",
            "deutschland": "germany",
            "espana": "spain",
            "españa": "spain",
            "italia": "italy",
            "nederland": "netherlands",
            "holland": "netherlands",
            "suisse": "switzerland",
            "schweiz": "switzerland",
            "österreich": "austria",
            "brasil": "brazil",
            "méxico": "mexico",
            "rsa": "south africa",
        }
        clean_country = _COUNTRY_ALIASES.get(clean_country, clean_country)
        locale = LOCALIZATION_MATRIX.get(clean_country)
        if not locale:
            for c_name, c_data in LOCALIZATION_MATRIX.items():
                if c_name in clean_country or clean_country in c_name:
                    locale = c_data
                    break
        if not locale:
            # Universal fallback for any global location
            locale = {
                "lang_code": "en",
                "tld": ".com",
                "niche_translations": {},
                "intent_triggers": ["Contact", "Inquiries", "Estimating", "Projects"],
                "contact_anchors": ["Contact Us", "About Us", "Office", "Team", "Direct"]
            }
        return locale

    @classmethod
    def generate_localized_queries(
        cls,
        country: str,
        city: str,
        niche: str,
        max_queries: int = 15
    ) -> List[Dict[str, str]]:
        """
        Generates authentic search queries using native idioms, localized syntax,
        and commercial intent operators across multiple progressive tiers.
        """
        clean_country = country.strip()
        clean_city = city.strip()
        clean_niche = niche.strip()
        n_lower = clean_niche.lower()

        locale = cls.resolve_country_profile(clean_country)
        lang_code = locale.get("lang_code", "en")
        tld = locale.get("tld", ".com")
        intents = locale.get("intent_triggers", ["Contact", "Projects"])
        anchors = locale.get("contact_anchors", ["Contact Us", "About Us"])

        # Resolve localized niche translation if available
        localized_niche = ""
        for n_key, n_trans in locale.get("niche_translations", {}).items():
            if n_key in n_lower or n_lower in n_key:
                localized_niche = n_trans
                break
        if not localized_niche:
            localized_niche = clean_niche

        construction_keywords = (
            "construction", "contractor", "hochbau", "tiefbau", "bâtiment",
            "building", "roofing", "mep", "tga", "civil", "infrastructure",
            "architecture", "architect", "engineering", "plumbing", "electrical",
            "bauunternehmen", "travaux", "edificación", "general contractors"
        )
        is_construction = any(ck in n_lower for ck in construction_keywords)

        queries: List[Dict[str, str]] = []

        if is_construction:
            # Construction-specific bidding/tender/estimating operators (broad recall first)
            queries.append({
                "type": "COMMERCIAL_CONTRACTOR_DIRECTORY",
                "query": f'{clean_niche} general contractors {clean_city} contact email',
                "language": "en",
                "description": f"General contractor directory search in {clean_city}"
            })
            queries.append({
                "type": "SUB_TRADE_INQUIRIES",
                "query": f'{clean_niche} contractors "{clean_city}" contact email',
                "language": "en",
                "description": f"Sub-trade commercial directory in {clean_city}"
            })
            queries.append({
                "type": "HIGH_INTENT_ESTIMATING",
                "query": f'"{localized_niche}" "{clean_city}" ("{intents[0]}" OR "{intents[1] if len(intents)>1 else intents[0]}")',
                "language": lang_code,
                "description": f"Targeting estimating & bidding departments in {clean_city}"
            })
            queries.append({
                "type": "DIRECT_CONTACT_DISCOVERY",
                "query": f'"{localized_niche}" "{clean_city}" "{anchors[0]}" "{anchors[1] if len(anchors)>1 else anchors[0]}" email',
                "language": lang_code,
                "description": f"Targeting corporate contact & directory pages in {clean_city}"
            })
            trigger_3 = intents[2] if len(intents) > 2 else intents[0]
            queries.append({
                "type": "PROCUREMENT_PORTAL",
                "query": f'"{localized_niche}" "{clean_city}" "{trigger_3}" ("@")',
                "language": lang_code,
                "description": f"Targeting procurement and tender submissions in {clean_city}"
            })
            anchor_lead = anchors[2] if len(anchors) > 2 else anchors[0]
            queries.append({
                "type": "LEADERSHIP_MAILTO",
                "query": f'"{localized_niche}" "{clean_city}" "{anchor_lead}" ("mailto:")',
                "language": lang_code,
                "description": f"Targeting mailto links on {clean_city} contractor sites"
            })
            queries.append({
                "type": "COMMERCIAL_FIRM_FALLBACK",
                "query": f'"{clean_niche}" firms "{clean_city}" "{clean_country}" contact phone email',
                "language": "en",
                "description": f"Sub-trade commercial directory in {clean_city}"
            })
        else:
            # Universal Multi-Niche Commercial queries (Luxury Real Estate, SaaS, Fitness, Medical, etc.)
            # Cloud-friendly broad recall queries FIRST
            queries.append({
                "type": "NICHE_BROAD_UNQUOTED",
                "query": f'{clean_niche} in "{clean_city}" "contact us"',
                "language": "en",
                "description": f"Broad contact recall for {clean_niche} in {clean_city}"
            })
            queries.append({
                "type": "NICHE_COMPANIES_CONTACT",
                "query": f'{clean_niche} {clean_city} contact email',
                "language": "en",
                "description": f"Broad email query for {clean_niche} in {clean_city}"
            })
            queries.append({
                "type": "NICHE_LOCAL_CONTACT",
                "query": f'"{clean_niche}" "{clean_city}" contact email',
                "language": lang_code,
                "description": f"Targeting verified {clean_niche} contact pages in {clean_city}"
            })
            queries.append({
                "type": "NICHE_COMMERCIAL_FIRM",
                "query": f'"{clean_niche}" ("agency" OR "company" OR "firm" OR "brokerage" OR "office" OR "services") "{clean_city}" email',
                "language": lang_code,
                "description": f"Targeting corporate {clean_niche} companies in {clean_city}"
            })
            queries.append({
                "type": "NICHE_INQUIRIES",
                "query": f'"{clean_niche}" "{clean_city}" ("contact us" OR "inquiries" OR "office" OR "info") email',
                "language": lang_code,
                "description": f"Targeting commercial inquiries for {clean_niche} in {clean_city}"
            })
            queries.append({
                "type": "NICHE_REGIONAL_OFFICIAL",
                "query": f'{clean_niche} {clean_city} {clean_country} official website',
                "language": "en",
                "description": f"Regional official websites for {clean_niche} in {clean_city}"
            })
            queries.append({
                "type": "NICHE_DIRECT_MAIL",
                "query": f'"{clean_niche}" "{clean_city}" "{clean_country}" "info@" OR "contact@"',
                "language": lang_code,
                "description": f"Targeting direct mail contacts for {clean_niche} in {clean_city}"
            })
            queries.append({
                "type": "NICHE_OFFICIAL_WEBSITE",
                "query": f'"{clean_niche}" in "{clean_city}" official website contact',
                "language": lang_code,
                "description": f"Targeting official websites for {clean_niche} in {clean_city}"
            })
            queries.append({
                "type": "NICHE_DIRECTORY_PARTNERS",
                "query": f'"{clean_niche}" "{clean_city}" directory OR members OR partners contact',
                "language": "en",
                "description": f"Industry directory & partner members in {clean_city}"
            })

        # Add localized native anchors if non-English
        if lang_code in ("de", "fr", "es", "it", "pt", "nl"):
            native_contact = anchors[0] if anchors else "contact"
            queries.append({
                "type": "NATIVE_LANGUAGE_CONTACT",
                "query": f'"{localized_niche}" "{clean_city}" ("{native_contact}" OR "email")',
                "language": lang_code,
                "description": f"Native language contact query for {clean_city}"
            })

        # Add targeted TLD query if specific ccTLD exists
        if tld and tld != ".com":
            queries.append({
                "type": "CCTLD_TARGETED",
                "query": f'"{clean_niche}" "{clean_city}" contact site:{tld}',
                "language": lang_code,
                "description": f"Targeting ccTLD {tld} for {clean_city}"
            })

        return queries[:max_queries]

    @classmethod
    def generate_query_batches(
        cls,
        country: str,
        city: str,
        niche: str,
        batch_size: int = 3
    ) -> List[List[Dict[str, str]]]:
        """Splits full localized query set into staged progressive batches for dynamic scaling."""
        all_q = cls.generate_localized_queries(country, city, niche, max_queries=15)
        batches: List[List[Dict[str, str]]] = []
        for i in range(0, len(all_q), batch_size):
            batches.append(all_q[i:i + batch_size])
        return batches


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
