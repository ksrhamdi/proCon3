# Single-page application, using javascript and AJAX.

# Import external modules.
import jinja2
import json
import logging
import os
import webapp2
# Import local modules.
from configAutocomplete import const as conf
import secrets
import user
# Import optional modules
try: import devConfiguration
except ImportError: pass


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
            'minLengthSurveyIntro': conf.minLengthSurveyIntro,
            'minLengthQuestion': conf.minLengthQuestion,
            'minLengthAnswer': conf.minLengthAnswer,
            'TOO_SHORT': conf.TOO_SHORT,
            'NO_COOKIE': conf.NO_COOKIE,
            'NO_LOGIN': conf.NO_LOGIN,
            'BAD_CRUMB': conf.BAD_CRUMB,
            'BAD_LINK': conf.BAD_LINK,
            'NOT_OWNER': conf.NOT_OWNER,
            'HAS_RESPONSES': conf.HAS_RESPONSES,
            'ERROR_DUPLICATE': conf.ERROR_DUPLICATE,
            'STOP_WORDS': json.dumps(  { w:True for w in conf.STOP_WORDS }  ) ,
            'loginApplicationId': secrets.loginApplicationId ,
            'LOGIN_URL': getattr(conf, 'LOGIN_URL_DEV', conf.LOGIN_URL) ,
            'IS_DEV':  'true' if conf.isDev  else 'false' ,

            # When page is loaded, user id may be generated, so recompute crumb.
            'crumb': user.createCrumb( userId ),
            'crumbForLogin': user.createCrumb( userIdForLogin, loginRequired=True ) if userIdForLogin  else ''
        }
        template = JINJA_ENVIRONMENT.get_template('main.html')
        self.response.write( template.render(templateValues) )


# Route URLs to page generators
app = webapp2.WSGIApplication(
    [
        ('/autocomplete/?', MainPage),
    ],
    debug=debug
)

