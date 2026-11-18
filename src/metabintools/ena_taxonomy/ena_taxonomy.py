import re
from typing import ClassVar

import requests
from loguru import logger


class EnaSubmittableTaxonomy:
    _query_cache: ClassVar[dict] = {}  # Cache for _ena_query_taxon results
    _suggest_cache: ClassVar[dict] = {}  # Cache for suggest-for-submission responses
    _lineage_cache: ClassVar[dict] = {}  # Cache for ena_suggest_lineage_taxid results

    def ena_suggest_lineage_taxid(self, lineage: str) -> dict:
        """
        Queries the ENA taxid service for possible taxids to submit to for
        a given lineage.

        Returns a dict containing the top suggested taxon matching the pattern:
        "(uncultured | unclassified ) <taxon name> (cyano)(bacterium|archaeon|sp)"

        Selects those without an "uncultured" prefix if available.

        Args:
            lineage: string representing an NCBI lineage (7-level format)

        Returns:
            dict: {taxId: int, scientificName: str}

        Raises:
            ValueError: if lineage cannot be parsed or no taxon found
            HTTPError: if ENA requests fail
        """
        # Check cache first
        if lineage in self._lineage_cache:
            return self._lineage_cache[lineage]

        lineage_split = re.findall(r"\w__([^;]*)", lineage)

        if not lineage_split or len(lineage_split) != 7:
            raise ValueError(f"Could not parse lineage: {lineage}")

        taxid_results = self._search_lineage_levels(lineage_split)

        if not taxid_results:
            taxid_results = self._search_uncultured_fallback(lineage_split)

        if not taxid_results:
            raise ValueError(f"Could not get a taxname for lineage: {lineage}")

        # Sort to prioritize non-uncultured names (sorted() avoids mutating cached lists)
        taxid_results = sorted(
            taxid_results, key=lambda x: "uncultured" in x["scientificName"].lower()
        )

        result = {
            "taxId": taxid_results[0]["taxId"],
            "scientificName": taxid_results[0]["scientificName"],
        }

        self._lineage_cache[lineage] = result
        return result

    def _search_lineage_levels(self, lineage_split: list) -> list:
        """Search lineage levels in order: species, genus, then higher levels."""
        kingdom = lineage_split[0]
        phylum = lineage_split[1]

        organism = self._get_organism_suffix(kingdom, phylum)

        # Search from most derived (species) to least derived
        for level, taxon in enumerate(lineage_split[::-1]):
            if not taxon:
                continue

            if level == 0:  # Species level
                results = self._ena_query_taxon(taxon)
            elif level == 1:  # Genus level
                results = self._ena_get_submittable_taxon(taxon, " sp.")
            else:  # Higher levels
                results = self._ena_get_submittable_taxon(taxon, organism)

            if results:
                return results

        return []

    def _search_uncultured_fallback(self, lineage_split: list) -> list:
        """Search for uncultured fallback taxon."""
        kingdom = lineage_split[0]
        phylum = lineage_split[1]

        organism = self._get_organism_suffix(kingdom, phylum)
        taxon = f"uncultured{organism}"
        return self._ena_query_taxon(taxon)

    def _get_organism_suffix(self, kingdom: str, phylum: str) -> str:
        """
        Determine the organism suffix based on kingdom and phylum.

        Args:
            kingdom: Kingdom name
            phylum: Phylum name

        Returns:
            str: organism suffix (' bacterium', ' archaeon', ' cyanobacterium')

        Raises:
            ValueError: if kingdom is not Bacteria or Archaea
        """
        if kingdom == "Bacteria":
            return " cyanobacterium" if phylum == "Cyanobacteria" else " bacterium"
        elif kingdom == "Archaea":
            return " archaeon"

        logger.warning(f"Cannot find submittable taxon for kingdom: {kingdom}")
        raise ValueError(f"Cannot find submittable taxon for kingdom: {kingdom}")

    def _ena_get_submittable_taxon(self, taxon: str, organism: str) -> list:
        """
        Query the ENA API to get a list of submittable taxids for a given taxon name.

        Args:
            taxon: taxon name
            organism: organism suffix string (e.g., ' bacterium', ' archaeon', ' sp.')

        Returns:
            List of dicts with taxId and scientificName, or empty list if none found

        Raises:
            HTTPError: if the request fails
        """
        search_space = [
            taxon,
            taxon + organism,
            "uncultured " + taxon + organism,
        ]

        for candidate in search_space:
            if candidate not in self._suggest_cache:
                url = f"https://www.ebi.ac.uk/ena/taxonomy/rest/suggest-for-submission/{candidate}"
                response = requests.get(url)
                response.raise_for_status()
                self._suggest_cache[candidate] = response.json()

            results = self._filter_ena_query(taxon, self._suggest_cache[candidate])
            if results:
                return results

        return []

    def _filter_ena_query(self, taxon: str, response: list) -> list:
        """
        Filter ENA query results to match only those with names like
        "uncultured Alphaproteobacteria bacterium".

        Args:
            taxon: Name of the taxon being queried
            response: List of dicts of suggested taxa from ENA

        Returns:
            Filtered list of matching taxa
        """
        tax_match = re.compile(
            rf"^(?:(uncultured|unclassified) )?{taxon} (cyano)?(bacterium|archaeon|sp\.)$"
        )

        return [x for x in response if tax_match.match(x.get("scientificName", ""))]

    def _ena_query_taxon(self, taxon: str) -> list:
        """
        Query an ENA taxon name by scientific name.

        Args:
            taxon: string representing an NCBI node name

        Returns:
            List containing a dict with taxId and scientificName, or empty list if not found

        Raises:
            HTTPError: if the request fails
        """
        # Check cache first
        if taxon in self._query_cache:
            return self._query_cache[taxon]

        url = f"https://www.ebi.ac.uk/ena/taxonomy/rest/scientific-name/{taxon}"
        response = requests.get(url)
        response.raise_for_status()

        data = response.json()
        result = [data[0]] if data else []

        self._query_cache[taxon] = result
        return result
