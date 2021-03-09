""" Mongo Database Wrapper for the apex-legends Session object """
from apex_legends.domain import Session


class SessionDB:
    """Instantiate this class and pass it an apex_legends Player object """
    def __init__(self, session: Session, user_name: str):

        # noinspection PyProtectedMember
        self._data = session._data
        self.session = session
        self.user_name = user_name

    def mongo_data(self) -> object:
        """ Returns all the data ready for ingestion into a mongo database """
        return {
            'user_name': self.user_name,
            'start_date': self.start_date,
            'end_date': self.end_date,
            '_data': self._data
        }

    def mongo_key(self):
        """ The 'key' fields for the mongo document """
        return {
            'user_name': self.user_name,
            'end_date': self.end_date
        }

    @property
    def is_active(self) -> bool:
        """ if the current session is active return True """
        return bool(self._data.get('metadata').get('isActive') == "True")

    @property
    def start_date(self):
        """ Convenience method for the session start date """
        return self._data.get('metadata').get('startDate').get('value')

    @property
    def end_date(self):
        """ Convenience method for the session end date """
        return self._data.get('metadata').get('endDate').get('value')
