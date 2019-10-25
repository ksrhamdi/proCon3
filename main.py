# Single-page application, using javascript and AJAX.
#     Separate page-displays for each proposal, versus expand/collapse.
#         + May be more understandable to users.
#         - Requires extra clicks to vote/reason even for small proposals.
#         + Allows smaller data fetches when number of proposals/reasons is large.
#
# cookie user-identity
#     Generate cookie anytime cookie is absent.
#     Store cookie in database only when user tries to store data.


# Import external modules
import json
import jinja2
import logging
import os
import webapp2
# Import local modules
from configuration import const as conf
import secrets
import user


# Parameters
debug = True
JINJA_ENVIRONMENT = jinja2.Environment(
    loader = jinja2.FileSystemLoader( os.path.dirname(__file__) ),
    extensions = ['jinja2.ext.autoescape'],
    autoescape = True
)


# Main page generator
class MainPage( webapp2.RequestHandler ):

    def get(self):
        # set cookie
        userId = user.getAndCreateBrowserIdCookie( self.request, self.response )
        userIdForLogin = user.getCookieId( self.request, loginRequired=True )

        templateValues = {
            # Pass configuration data from server to client.
            'minLengthRequest': conf.minLengthRequest,
            'minLengthProposal': conf.minLengthProposal,
            'minLengthReason': conf.minLengthReason,
            'TOO_SHORT': conf.TOO_SHORT,
            'REASON_TOO_SHORT': conf.REASON_TOO_SHORT,
            'NO_COOKIE': conf.NO_COOKIE,
            'NO_LOGIN': conf.NO_LOGIN,
            'BAD_CRUMB': conf.BAD_CRUMB,
            'BAD_LINK': conf.BAD_LINK,
            'NOT_OWNER': conf.NOT_OWNER,
            'HAS_RESPONSES': conf.HAS_RESPONSES,
            'STOP_WORDS': json.dumps(  { w:True for w in conf.STOP_WORDS }  ) ,
            'VOTER_ID_LOGIN_SIG_LENGTH': conf.VOTER_ID_LOGIN_SIG_LENGTH ,
            'VOTER_ID_LOGIN_REQUEST_ID_LENGTH': conf.VOTER_ID_LOGIN_REQUEST_ID_LENGTH ,
            'loginApplicationId': secrets.loginApplicationId ,
            'LOGIN_URL':  conf.LOGIN_URL_DEV if conf.isDev  else conf.LOGIN_URL ,
            'IS_DEV':  'true' if conf.isDev  else 'false' ,

            # When page is loaded, user id may be generated, so recompute crumb.
            'crumb': user.createCrumb( userId ) if userId  else '' ,
            'crumbForLogin': user.createCrumb( userIdForLogin, loginRequired=True ) if userIdForLogin  else ''
        }
        template = JINJA_ENVIRONMENT.get_template('main.html')
        self.response.write( template.render(templateValues) )


# Route URLs to page generators
app = webapp2.WSGIApplication(
    [
        ('/procon', MainPage),
    ],
    debug=debug
)

