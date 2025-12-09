"""Supplier discovery service using SerpAPI for real Google searches."""
from typing import List, Dict
from sqlalchemy.orm import Session
import re
from urllib.parse import urlparse

from app.models.discovered_supplier import DiscoveredSupplier
from app.models.medicine import Medicine
from app.config import settings
import logging

logger = logging.getLogger(__name__)

try:
    from serpapi import GoogleSearch
    SERPAPI_AVAILABLE = True
except ImportError:
    SERPAPI_AVAILABLE = False
    logger.warning("SerpAPI not installed. Using fallback mode.")


class SupplierDiscoveryService:
    """Discover real pharmaceutical suppliers via Google search (SerpAPI)."""
    
    def __init__(self, db: Session, demo_mode: bool = True):
        self.db = db
        self.demo_mode = demo_mode
        self.demo_recipient = "kanhacet@gmail.com"
        self.serpapi_key = settings.SERPAPI_KEY if hasattr(settings, 'SERPAPI_KEY') else None
    
    def discover_suppliers(
        self,
        medicine: Medicine,
        quantity: int,
        procurement_task_id: int = None
    ) -> List[DiscoveredSupplier]:
        """
        Discover suppliers via Google search using SerpAPI.
        Falls back to simulated data if SerpAPI unavailable.
        """
        
        logger.info(f"🔍 Discovering suppliers for {medicine.name}...")
        
        # Try SerpAPI first
        if SERPAPI_AVAILABLE and self.serpapi_key:
            suppliers = self._discover_via_serpapi(medicine, quantity, procurement_task_id)
            if suppliers:
                return suppliers
        
        # Fallback to simulated data
        logger.warning("Using simulated suppliers (SerpAPI not configured)")
        return self._discover_simulated(medicine, quantity, procurement_task_id)
    
    def _discover_via_serpapi(
        self,
        medicine: Medicine,
        quantity: int,
        procurement_task_id: int
    ) -> List[DiscoveredSupplier]:
        """Search Google for real suppliers using SerpAPI."""
        
        search_query = f"{medicine.name} pharmaceutical supplier India wholesale bulk"
        logger.info(f"🔍 Searching Google: '{search_query}'")
        
        try:
            params = {
                "q": search_query,
                "location": "India",
                "hl": "en",
                "gl": "in",
                "num": 10,
                "api_key": self.serpapi_key
            }
            
            search = GoogleSearch(params)
            results = search.get_dict()
            organic_results = results.get("organic_results", [])
            
            if not organic_results:
                logger.warning("No search results from SerpAPI")
                return []
            
            logger.info(f"✓ Found {len(organic_results)} search results")
            
            discovered = []
            
            for rank, result in enumerate(organic_results[:5], 1):  # TOP 5 ONLY
                title = result.get("title", "")
                link = result.get("link", "")
                snippet = result.get("snippet", "")
                
                # Extract company name from title
                company_name = self._extract_company_name(title)
                
                # Extract domain
                domain = self._extract_domain(link)
                
                # Guess email from domain
                display_email = self._guess_email(domain)
                
                # Extract location from snippet
                location = self._extract_location(snippet)
                
                # Generate demo identifier
                demo_id = company_name.split()[0][:15] if company_name else f"Supplier{rank}"
                
                # Check if already exists
                existing = self.db.query(DiscoveredSupplier).filter_by(
                    website=link
                ).first()
                
                if existing:
                    discovered.append(existing)
                    continue
                
                # Create supplier
                supplier = DiscoveredSupplier(
                    name=company_name,
                    website=link,
                    display_email=display_email,
                    actual_email=self.demo_recipient if self.demo_mode else display_email,
                    location=location,
                    demo_identifier=demo_id,
                    search_query=search_query,
                    search_rank=rank,
                    found_via_search=True,
                    is_demo_mode=self.demo_mode,
                    procurement_task_id=procurement_task_id
                )
                
                self.db.add(supplier)
                self.db.commit()
                self.db.refresh(supplier)
                
                logger.info(f"✓ Discovered: {supplier.name} - {supplier.display_email}")
                discovered.append(supplier)
            
            return discovered
            
        except Exception as e:
            logger.error(f"SerpAPI search failed: {e}")
            return []
    
    def _discover_simulated(
        self,
        medicine: Medicine,
        quantity: int,
        procurement_task_id: int
    ) -> List[DiscoveredSupplier]:
        """Fallback: Create simulated suppliers for demo."""
        
        suppliers_data = [
            {"name": "MedPharma Solutions", "domain": "medpharma.com", "location": "Mumbai", "id": "MedPharma"},
            {"name": "HealthCare Suppliers", "domain": "healthcaresuppliers.in", "location": "Delhi", "id": "HealthCare"},
            {"name": "QuickMeds Distributors", "domain": "quickmeds.in", "location": "Bangalore", "id": "QuickMeds"},
            {"name": "ABC Pharmaceuticals", "domain": "abcpharma.in", "location": "Pune", "id": "ABCPharma"},
            {"name": "HealthFirst Supplies", "domain": "healthfirst.co.in", "location": "Chennai", "id": "HealthFirst"}
        ]  # TOP 5 SUPPLIERS ONLY
        
        discovered = []
        
        for rank, data in enumerate(suppliers_data, 1):
            existing = self.db.query(DiscoveredSupplier).filter_by(
                demo_identifier=data["id"]
            ).first()
            
            if existing:
                discovered.append(existing)
                continue
            
            supplier = DiscoveredSupplier(
                name=data["name"],
                website=f"https://{data['domain']}",
                display_email=f"sales@{data['domain']}",
                actual_email=self.demo_recipient if self.demo_mode else f"sales@{data['domain']}",
                location=f"{data['location']}, India",
                demo_identifier=data["id"],
                search_query=f"{medicine.name} supplier India",
                search_rank=rank,
                found_via_search=True,
                is_demo_mode=self.demo_mode,
                procurement_task_id=procurement_task_id
            )
            
            self.db.add(supplier)
            self.db.commit()
            self.db.refresh(supplier)
            
            discovered.append(supplier)
        
        return discovered
    
    def _extract_company_name(self, title: str) -> str:
        """Extract company name from search result title."""
        # Remove common suffixes
        title = re.sub(r'\s*[-|]\s*.*$', '', title)
        return title.strip()[:255]
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.replace('www.', '')
            return domain
        except:
            return ""
    
    def _guess_email(self, domain: str) -> str:
        """Guess email address from domain."""
        if not domain:
            return "info@example.com"
        return f"sales@{domain}"
    
    def _extract_location(self, snippet: str) -> str:
        """Extract location from snippet text."""
        indian_cities = [
            "Mumbai", "Delhi", "Bangalore", "Hyderabad", "Chennai",
            "Kolkata", "Pune", "Ahmedabad", "Jaipur"
        ]
        
        for city in indian_cities:
            if city.lower() in snippet.lower():
                return f"{city}, India"
        
        return "India"
