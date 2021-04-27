""" A helper module for the apex legends API """
import os
from dotenv import load_dotenv
from apex_legends_api import ApexLegendsAPI

load_dotenv()

# pylint disable=too-few-public-methods
class ApexAPIHelper:  # noqa R0903
    """ Wrapper class for the Apex API to add a few helper methods """
    def __init__(self):
        self.api: ApexLegendsAPI = ApexLegendsAPI(api_key=os.getenv('APEX_LEGENDS_API_KEY'))
