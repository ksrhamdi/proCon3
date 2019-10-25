import base64
from configuration import const as conf
from constants import Constants
import json
import logging


# Constants
const = Constants()
const.COOKIE_NAME = 'C'
const.COOKIE_NAME_FOR_JAVASCRIPT = 'J'

# Returns cookieData:map[name->value]
def getCookieData( httpRequest ):
    if conf.isDev:  logging.debug( 'httpRequest.cookies=' + str(httpRequest.cookies) )
    cookieBase64 = httpRequest.cookies.get( const.COOKIE_NAME )
    cookieBase64 = cookieBase64.encode('ascii') if cookieBase64  else None

    cookieJson = base64.urlsafe_b64decode( cookieBase64 ) if cookieBase64  else None
    logging.debug( 'cookieJson=' + str(cookieJson) )
    try:
        return json.loads( cookieJson ) if cookieJson  else {}
    except:
        return {}


# old/newCookieData:map[key->value]
# Modifies httpResponse
# Returns mergedCookieData : map[key->value]
def setCookieData( oldCookieData, newCookieData, useSecureCookie, httpResponse ):

    # merge in new fields
    mergedCookieData = oldCookieData.copy()
    mergedCookieData.update( newCookieData )

    # Put all data into server-only (httponly) cookie
    setCookieNameToValues( const.COOKIE_NAME, mergedCookieData, httpResponse, secure=useSecureCookie, httponly=useSecureCookie )
    
    # Copy only data needed by browser into browser-accessible cookie
    mergedCookieDataForJavascript = {
        'city': mergedCookieData.get( conf.COOKIE_FIELD_VOTER_CITY, None ) ,
        'hasVoterId': bool( mergedCookieData.get( conf.COOKIE_FIELD_VOTER_ID, False ) )
    }
    setCookieNameToValues( const.COOKIE_NAME_FOR_JAVASCRIPT, mergedCookieDataForJavascript, httpResponse, secure=useSecureCookie, httponly=False )

    return mergedCookieData


def setCookieNameToValues( cookieName, cookieKeyToValue, httpResponse, secure=True, httponly=True ):
    cookieJson = json.dumps( cookieKeyToValue )
    logging.debug( 'cookie.setCookieNameToValues() cookieJson=' + cookieJson )

    cookieBase64 = base64.urlsafe_b64encode( cookieJson )
    httpResponse.set_cookie( cookieName, cookieBase64, secure=secure, httponly=httponly )




#################################################################################
# Unit test

import unittest

class TestCookie(unittest.TestCase):

    class CookiesMock:
        def get( self, cookieName ):
            return 'eyJiIjoiQiJ9'

    class RequestMock:
        def __init__(self): self.cookies = TestCookie.CookiesMock()
        
    class ResponseMock:
        def set_cookie( self, cookieName, cookieJson, secure=True, httponly=True ):
            self.cookieJson = cookieJson

    def test( self ):
        mock_Request = TestCookie.RequestMock()
        # Test getting and parsing cookie
        oldCookieData = getCookieData( mock_Request )
        self.assertEqual( {'b':'B'} , oldCookieData )
        
        # Test setting and serializing cookie
        newCookieData = { 'a':'A' }
        mock_Response = TestCookie.ResponseMock()
        useSecureCookie = False
        mergedCookieData = setCookieData( oldCookieData, newCookieData, useSecureCookie, mock_Response )
        self.assertEqual( 
            'eyJhIjogIkEiLCAiYiI6ICJCIn0=',
            mock_Response.cookieJson )

if __name__ == '__main__':
    unittest.main()

