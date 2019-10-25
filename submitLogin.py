# Services to get voter-id login cookie
# 
# If abuser steals browser-cookie... 
#   Only send open-voter-id cookie with first client-response
#   Can request login and possibly get voter-id from logged-in user who never returned after login
#     Need timeout
#   Can request logout... and fail because no crumb?
#     Logged-in user cannot logout if login-crumb lost, until page-refresh re-sends login-crumb? Ok?


# Import external modules
from google.appengine.ext import ndb
import jinja2
import json
import logging
import os
import re
import time
import urllib
import urlparse
import webapp2
# Import app modules
import browser
import cookie
from configuration import const as conf
import httpServer
import linkKey
import user



# Parameters
JINJA_ENVIRONMENT = jinja2.Environment(
    loader = jinja2.FileSystemLoader( os.path.dirname(__file__) ),
    extensions = ['jinja2.ext.autoescape'],
    autoescape = True
)


class SignLoginRequest(webapp2.RequestHandler):

    def post(self):

        logging.debug( 'SignLoginRequest.post() request.body=' + self.request.body )

        # Collect inputs
        requestLogId = os.environ.get( conf.REQUEST_LOG_ID )
        responseData = { 'success':False, 'requestLogId':requestLogId }
        inputData = json.loads( self.request.body )
        logging.debug( 'SignLoginRequest.post() inputData=' + str(inputData) )

        browserCrumb = inputData.get( 'crumb', '' )
        logging.debug( 'SignLoginRequest.post() browserCrumb=' + str(browserCrumb) )

        loginRequestId = user.randomStringWithLength( conf.VOTER_ID_LOGIN_REQUEST_ID_LENGTH )
        signature = user.signLoginRequest( loginRequestId )

        # Store login-request-id, to later check against spoofed login-return
        browserId = user.getCookieId( self.request, loginRequired=False )
        if not browserId:  httpServer.outputJsonError( conf.NO_COOKIE, responseData, self.response );  return;
        browserRecord = browser.BrowserRecord.get_by_id( browserId )
        logging.debug( 'LoginReturn.post() browserRecord=' + str(browserRecord) )

        if not browserRecord:
            browserRecord = browser.BrowserRecord( id=browserId )
        now = int( time.time() )
        browserRecord.loginRequestTime = now
        browserRecord.voterLoginRequestId = loginRequestId
        browserRecord.put()

        responseData.update(  { 'success':True , 'loginRequestId':loginRequestId, 'signature':signature }  )
        self.response.out.write( json.dumps( responseData ) )



# Login receiving service, storing browserId+requestId->loginId with 10-minute expiration time
class LoginReturn(webapp2.RequestHandler):

    def post(self):

        logging.debug( 'LoginReturn.post() request.body=' + self.request.body )

        # Collect inputs
        requestLogId = os.environ.get( conf.REQUEST_LOG_ID )
        responseData = { 'success':False, 'requestLogId':requestLogId }
        inputData = urlparse.parse_qs( self.request.body )
        logging.debug( 'LoginReturn.post() inputData=' + str(inputData) )

        requestId = inputData['requestId'][0]
        responseSignature = inputData['responseSignature'][0]
        voterId = inputData[conf.COOKIE_FIELD_VOTER_ID][0]
        city = inputData['city'][0]

        # Check that browser-id exists
        # Cannot check browser crumb, because crumb does not exist in this login-result page's javascript
        browserId = user.getCookieId( self.request, loginRequired=False )
        if not browserId:  httpServer.outputJsonError( conf.NO_COOKIE, responseData, self.response );  return;

        # Check responseSignature
        expectedResponseSignature = user.signLoginResult( requestId, voterId, city )
        logging.debug( 'LoginReturn.post() expectedResponseSignature=' + str(expectedResponseSignature) )
        if (responseSignature != expectedResponseSignature):  httpServer.outputJsonError( 'responseSignature does not match expected', responseData, self.response );  return;

        # Check stored browserId -> loginRequestId , check timeout, then delete record
        browserRecord = browser.BrowserRecord.get_by_id( browserId )
        logging.debug( 'LoginReturn.post() browserRecord=' + str(browserRecord) )
        
        now = int( time.time() )
        if browserRecord.voterLoginRequestId != requestId:  httpServer.outputJsonError( 'login requestId does not match expected', responseData, self.response );  return;
        if browserRecord.loginRequestTime + conf.VOTER_ID_TIMEOUT_SEC < now:  httpServer.outputJsonError( 'login past timeout', responseData, self.response );  return;

        browserRecordKey = ndb.Key( browser.BrowserRecord, browserId )
        browserRecordKey.delete()

        # Send login-id to browser now, with response-page cookie, instead of server storing a mapping
        # To set crumbForLogin into original page's javascript variable, have to use separate getLoginCrumb call

        # Add voter-id to persistent cookie
        oldCookieData = cookie.getCookieData( self.request )
        newCookieField = { conf.COOKIE_FIELD_VOTER_ID:voterId , conf.COOKIE_FIELD_VOTER_CITY:city }
        useSecureCookie = user.getUseSecureCookie( self.request )
        newCookieData = cookie.setCookieData( oldCookieData, newCookieField, useSecureCookie, self.response )
        logging.debug( 'GetLogin() newCookieData=' + str(newCookieData) )

        responseData.update( {
            'crumbForLogin': user.createCrumb( voterId, loginRequired=True ) ,
            'city': city
        } )

        # Send page that closes tab
        template = JINJA_ENVIRONMENT.get_template('loginReturn.html')
        self.response.write(  template.render( responseData )  )
        return None




# Login-cookie already sent in loginReturn page
# Login-crumb would be resent with page-reload
class GetLoginCrumb( webapp2.RequestHandler ):
    def get( self ):

        logging.debug( 'GetLogin()' )

        # Collect inputs
        requestLogId = os.environ.get( conf.REQUEST_LOG_ID )
        responseData = { 'success':False, 'requestLogId':requestLogId }
        # Since this is a HTTP-GET call, browser-crumb should not be sent since it would be public

        browserId = user.getCookieId( self.request )
        if not browserId:  httpServer.outputJsonError( conf.NO_COOKIE, responseData, self.response );  return;

        loginId = user.getCookieId( self.request, loginRequired=True )
        if not loginId:  httpServer.outputJsonError( 'No login cookie', responseData, self.response );  return;

        responseData.update( {
            'success': True ,
            'crumbForLogin': user.createCrumb( loginId, loginRequired=True )
        } )

        logging.debug( 'GetLogin() responseData=' + json.dumps(responseData, indent=4, separators=(', ' , ':')) )
        self.response.out.write( json.dumps( responseData ) )




# Login-crumb not required to allow user to logout even if browser crumb is lost.
# Browser-crumb can be required for logout, since browser-crumb can be regenerated by page reload.
class SubmitLogout(webapp2.RequestHandler):

    def post(self):

        logging.debug( 'SubmitLogout.post() request.body=' + self.request.body )

        # Collect inputs
        requestLogId = os.environ.get( conf.REQUEST_LOG_ID )
        responseData = { 'success':False, 'requestLogId':requestLogId }
        inputData = json.loads( self.request.body )
        logging.debug( 'SubmitLogout.post() inputData=' + str(inputData) )

        browserCrumb = inputData.get( 'crumb', '' )
        loginCrumb = inputData.get( 'crumbForLogin', '' )
        logging.debug( 'SubmitLogout.post() browserCrumb=' + str(browserCrumb) + ' loginCrumb=' + str(loginCrumb) )

        browserId = httpServer.getAndCheckUserId( self.request, browserCrumb, responseData, self.response, loginRequired=False )
        if not browserId:  return

        # Remove voter-id from persistent cookie, even if cookie is already invalid
        oldCookieData = cookie.getCookieData( self.request )
        newCookieField = { conf.COOKIE_FIELD_VOTER_ID:None , conf.COOKIE_FIELD_VOTER_CITY:None }
        useSecureCookie = user.getUseSecureCookie( self.request )
        newCookieData = cookie.setCookieData( oldCookieData, newCookieField, useSecureCookie, self.response )
        logging.debug( 'SubmitLogout() newCookieData=' + str(newCookieData) )

        responseData.update(  { 'success':True }  )
        self.response.out.write( json.dumps( responseData ) )



# Route HTTP request
app = webapp2.WSGIApplication([
    ('/signLoginRequest', SignLoginRequest),
    ('/loginReturn', LoginReturn),
    ('/getLogin' , GetLoginCrumb),
    ('/submitLogout', SubmitLogout)
])


