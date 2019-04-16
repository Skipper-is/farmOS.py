from urllib.parse import urlparse, parse_qs

from .session import APISession

class BaseAPI(object):
    """Base class for API methods

    This class includes basic implementations of the
    get(), send() and delete() methods used in the API client.

    Keyword Arguments:
    session: APISession for the farmOS instance
    entity_type: String, used to set the entity type in the path
        of all requests used with the API
    """

    def __init__(self, session, entity_type=None):
        self.session = session
        self.entity_type = entity_type
        self.filters = {}

    def _get_single_record_data(self, id):
        """Retrieve one record given the record ID"""
        # Set path to return record type by specific ID
        path = self.entity_type + '/' + str(id) + '.json'

        response = self.session.http_request(path=path)

        if (response.status_code == 200):
            return response.json()

        return []

    def _get_record_data(self, filters={}):
        """Retrieve one page of raw record data from the farmOS API."""
        # Set path to return record type + filters
        path = self.entity_type + '.json'
        # Combine instance filters and filters from the method call
        filters = {**self.filters, **filters}

        response = self.session.http_request(path=path, params=filters)

        if (response.status_code == 200):
            return response.json()

        return []

    def _get_all_record_data(self, page=0, filters={}, list=None):
        """Recursive function to retrieve multiple pages of raw record data from the farmOS API."""
        if list is None:
            list = []
            
        filters['page'] = page

        data = self._get_record_data(filters=filters)

        # Append record data to list of all requested data
        if ('list' in data):
            list = list + data['list']

        # Check to see if there are more pages
        if ('last' in data):
            parsed_url = urlparse(data['last'])
            last_page = parse_qs(parsed_url.query)['page'][0]
            # Last page, return the list
            if (last_page == page):
                return list
            # Recursive call, get the next page
            else:
                return self._get_all_record_data(list=list, page=(page+1), filters=filters)

        return list

    def _get_records(self, filters={}):
        """Helper function that checks to retrieve one record, one page or multiple pages of farmOS records"""

        # Determine if filters is an int (id) or dict (filters object)
        if isinstance(filters, int) or isinstance(filters, str):
            data = self._get_single_record_data(filters)
        elif isinstance(filters, dict):
            # Check if the caller requests a specific page
            if 'page' in filters:
                print('special page' + str(filters['page']))
                data = self._get_record_data(filters=filters)
                if 'list' in data:
                    return data['list']
                else:
                    return data
            else:
                data = self._get_all_record_data(filters=filters)

        return data

    def get(self, filters=None):
        """Simple get method"""
        if filters is None:
            filters = {}

        data = self._get_records(filters=filters)

        return data

    def send(self, payload):
        options = {}
        options['json'] = payload

        # If an ID is included, update the record
        id = payload.pop('id', None)
        if id:
            path = self.entity_type + '/' + str(id)
            response = self.session.http_request(method='PUT', path=path, options=options)
        # If no ID is included, create a new record
        else:
            path = self.entity_type
            response = self.session.http_request(method='POST', path=path, options=options)

        if (response.status_code == 201):
            return response.json()

        return []

    def delete(self, id):
        path = self.entity_type + '/' + str(id)
        response = self.session.http_request(method='DELETE', path=path)

        return response

class TermAPI(BaseAPI):
    """API for interacting with farm Terms"""

    def __init__(self, session):
        # Define 'taxonomy_term' as the farmOS API entity endpoint
        super().__init__(session=session, entity_type='taxonomy_term')

    def get(self, filters={}):
        """Get method that supports a bundle name as the 'filter' parameter"""

        # Check if filters parameter is a str
        if isinstance(filters, str):
            # Add filters to instance requests.session filter dict with keyword 'bundle'
            self.filters['bundle'] = filters
            # Reset filters to empty dict
            filters = {}

        data = self._get_records(filters=filters)

        return data

class LogAPI(BaseAPI):
    """API for interacting with farm logs"""

    def __init__(self, session):
        # Define 'log' as the farmOS API entity endpoint
        super().__init__(session=session, entity_type='log')

class AssetAPI(BaseAPI):
    """API for interacting with farm assets"""

    def __init__(self, session):
        # Define 'farm_asset' as the farmOS API entity endpoint
        super().__init__(session=session, entity_type='farm_asset')

class AreaAPI(TermAPI):
    """API for interacting with farm areas, a subset of farm terms"""

    def __init__(self, session):
        super().__init__(session=session)
        self.filters['bundle'] = 'farm_areas'

    def get(self, filters={}):
        """Retrieve raw record data from the farmOS API.

        Override get() from BaseAPI to support TID (Taxonomy ID)
        rather than record ID
        """

        # Determine if filters is an int (tid) or dict (filters object)
        if isinstance(filters, int) or isinstance(filters, str):
            tid = str(filters)
            # Add tid to filters object
            filters = {
                'tid':tid
            }

        data = self._get_records(filters=filters)

        return data
