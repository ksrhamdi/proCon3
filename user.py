# Import external modules
import base64
import hashlib
import hmac
import logging
import random
import re
import string
import time
# Import app modules
from configuration import const as conf
from constants import Constants
import cookie
import secrets


########################################################################
# Constants

const = Constants()
const.ID_COOKIE_LENGTH = 50



########################################################################
# Signature functions

def signLoginRequest( loginRequestKey ):
    return loginRequestSignature( secrets.loginRequestSigningSecret, loginRequestKey, secrets.loginApplicationId )

def signLoginResult( loginRequestKey, voterId, city ):
    return loginResponseSignature( secrets.loginResponseSigningSecret, loginRequestKey, secrets.loginApplicationId, voterId, city )


def loginRequestSignature( applicationRequestSigningSecret, requestId, applicationId ):
    if (not requestId) or (not applicationId) or (not applicationRequestSigningSecret):  return None
    return hashForSignature( applicationRequestSigningSecret , requestId + applicationId )

def loginResponseSignature( applicationResponseSigningSecret, requestId, applicationId, voterId, city ):
    if (not requestId) or (not applicationId) or (not voterId) or (not city) or (not applicationResponseSigningSecret):
        return None
    return hashForSignature( applicationResponseSigningSecret , requestId + applicationId + voterId + city )

def hashForSignature( secret, data ):
    return base64.b32encode( hmac.new(secret, data, digestmod=hashlib.sha512).digest() )




########################################################################
# crumb functions

def createCrumb( userId, loginRequired=False ):
    hasher = hashlib.md5()
    salt = secrets.crumbSaltForLogin if loginRequired  else secrets.crumbSalt
    hasher.update( userId + salt )
    return hasher.hexdigest()[:10]

def checkCrumb( userId, browserCrumb, loginRequired=False, loginCrumb=None ):
    expectedCrumb = createCrumb( userId, loginRequired=loginRequired )
    
    inputCrumb = loginCrumb if loginRequired  else browserCrumb
    logging.debug( 'user.checkCrumb() inputCrumb=' + str(inputCrumb) )
    logging.debug( 'user.checkCrumb() expectedCrumb=' + str(expectedCrumb) )
    
    return (expectedCrumb == inputCrumb)



########################################################################
# cookie id functions

randomGenerator = random.SystemRandom()

def randomStringWithLength( length ):
    characters = string.ascii_uppercase + string.ascii_lowercase + string.digits
    return ''.join( randomGenerator.choice(characters) for _ in range(length) )

def generateCookieId():
    return randomStringWithLength( const.ID_COOKIE_LENGTH )



# Return browserId, voterId ?

def getCookieId( httpRequest, loginRequired=False ):
    # returns identity:string or null
    cookieData = cookie.getCookieData( httpRequest )
    logging.debug( 'getCookieId() loginRequired=' + str(loginRequired) + ' cookieData=' + str(cookieData) )

    browserId = cookieData.get( conf.COOKIE_FIELD_BROWSER_ID, None )
    voterId = cookieData.get( conf.COOKIE_FIELD_VOTER_ID, None )
    return  voterId if loginRequired  else browserId



def setCookieId( id, useSecureCookie, httpResponse ):
    # modifies httpResponse
    cookie.setCookieData( {}, {conf.COOKIE_FIELD_BROWSER_ID:id}, useSecureCookie, httpResponse )

# No longer used, since it can leave cookies in an invalid state
def getOrCreateBrowserIdCookie( httpRequest, httpResponse ):
    userId = getCookieId( httpRequest, loginRequired=False )
    logging.debug( 'user.getOrCreateBrowserIdCookie() httpRequest.host=' + str(httpRequest.host) )
    logging.debug( 'user.getOrCreateBrowserIdCookie() userId=' + str(userId) )
    if userId is None:
        userId = generateCookieId()
        logging.debug( 'user.getOrCreateBrowserIdCookie() userId=' + userId )

        useSecureCookie = getUseSecureCookie( httpRequest )
        setCookieId( userId, useSecureCookie, httpResponse )

    return userId

def getAndCreateBrowserIdCookie( httpRequest, httpResponse ):
    userId = getCookieId( httpRequest, loginRequired=False )
    if userId is None:  userId = generateCookieId()
    useSecureCookie = getUseSecureCookie( httpRequest )
    setCookieId( userId, useSecureCookie, httpResponse )
    return userId

# To-do: Remove argument httpRequest, and propagate change through callers
def getUseSecureCookie( httpRequest ):
    return not conf.isDev



##########################################################################
# recently viewed requests/proposals

def updateRecent( valueToTime, newValue, newTime, maxValues ):
    # valueToTime:map[value -> time]

    # add new value 
    valueToTime[ newValue ] = newTime
    # while we have too many values... 
    while len(valueToTime.keys()) > maxValues:
        # remove oldest value
        minTimeValue = min( valueToTime, key=valueToTime.get )
        del valueToTime[ minTimeValue ]


# Stores recent linkKeys in cookie. Modifies httpResponse.
def storeRecentLinkKey( linkKey, httpRequest, httpResponse ):
    # Read old cookie field from httpRequest.
    oldCookieData = cookie.getCookieData( httpRequest )
    recentLinkKeys = oldCookieData.get( conf.COOKIE_FIELD_RECENTS, {} )
    # Set new cookie field in httpResponse.
    now = int( time.time() )
    updateRecent( recentLinkKeys, linkKey, now, conf.recentRequestsMax )
    newCookieData = {  conf.COOKIE_FIELD_RECENTS: recentLinkKeys  }
    useSecureCookie = getUseSecureCookie( httpRequest )
    cookie.setCookieData( oldCookieData, newCookieData, useSecureCookie, httpResponse )


# Retrieves recent linkKeys from cookie.
def retrieveRecentLinkKeys( httpRequest ):
    # Read old cookie field from httpRequest.
    oldCookieData = cookie.getCookieData( httpRequest )
    return oldCookieData.get( conf.COOKIE_FIELD_RECENTS, {} )



#################################################################################
# Unit test

import unittest

class TestUser(unittest.TestCase):

    class RequestAndResponseMock:
        def __init__(self): self.cookies = {}
        
        def set_cookie( self, cookieName, cookieJson, secure=True, httponly=True ):
            self.cookies[ cookieName ] = cookieJson


    def test(self):
        httpRequest = TestUser.RequestAndResponseMock()
        httpResponse = httpRequest
        
        # Test crumb
        userId = 'USER_ID'
        crumb = createCrumb( userId )
        self.assertTrue( checkCrumb( userId, crumb ) )
        
        # Test cookie id
        id = generateCookieId()
        self.assertEqual( const.ID_COOKIE_LENGTH, len(id) )
        useSecureCookie = False
        setCookieId( id, useSecureCookie, httpResponse )
        self.assertEqual( id, getCookieId(httpRequest, False) )

        # Test recent values update
        valueToTime = { '0':0, '1':1, '2':2 }
        maxValues = 5
        updateRecent( valueToTime, '3', 3, maxValues )
        updateRecent( valueToTime, '4', 4, maxValues )
        updateRecent( valueToTime, '5', 5, maxValues )
        self.assertEqual( maxValues, len(valueToTime) )

if __name__ == '__main__':
    unittest.main()

