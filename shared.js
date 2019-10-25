///////////////////////////////////////////////////////////////////////////////////////
// Constants

const EVENT_NAMES = ['click', 'focus', 'blur', 'keydown', 'keyup', 'paste', 'input', 'invalid', 'mousedown'];
const RED = 'red';
const BLACK = 'black';
const GREEN = 'green';
const GREY = 'grey';

const MESSAGE_NO_COOKIE = 'No user identity found. Try reloading the page.';
const MESSAGE_BAD_CRUMB = 'User action unverified. Please retry.';

const KEY_NAME_ENTER = 'Enter'
const KEY_NAME_ESCAPE = 'Escape'
const KEY_NAME_SPACE = ' '



///////////////////////////////////////////////////////////////////////////////////////
// Element access

    function
elementWithId( id ){  return document.getElementById( id );  }

    function
elementsWithClass( className ){  return document.getElementsByClassName( className );  }

                

///////////////////////////////////////////////////////////////////////////////////////
// Fragments

    function
setFragmentFields( newKeyToValue ){
    // Merge with existing fragment.
    oldKeyToValue = parseFragment();
    mergedKeyToValue = {};
    for (var key in oldKeyToValue) {
        mergedKeyToValue[key] = oldKeyToValue[key];
    }
    for (var key in newKeyToValue) {
        var value = newKeyToValue[key];
        if ( value === null  &&  key in mergedKeyToValue ){  delete mergedKeyToValue[key];  }
        else if ( value !== null ){  mergedKeyToValue[key] = value;  }
    }
    setWholeFragment( mergedKeyToValue );
}

    function
setWholeFragment( keyToValue ){
    // Join keys and values with URI encoding.
    var encoded = '';
    for (var key in keyToValue) {
        var value = keyToValue[key];
        var keyValueStr = key + '=' + value;
        if ( encoded !== '' ){  encoded += '&';  }
        encoded += keyValueStr;
    }
    window.location.hash = encoded;
}

    function
parseFragment( ){
    // Split key-value pairs by '&'
    // Split each key-value pair by '='
    keyToValue = {};
    var encoded = window.location.hash;
    encoded = encoded.replace( new RegExp('^#'), '' );  // Trim leading '#'.
    if ( ! encoded ){  return keyToValue;  }
    keyValueStrings = encoded.split('&');
    for ( var k = 0;  k < keyValueStrings.length;  ++k ){
        var keyAndValue = keyValueStrings[k].split('=');
        var key = keyAndValue[0];
        var value = keyAndValue[1];
        keyToValue[key] = value;
    }
    return keyToValue;
}


    function
objectsEqual( obj1, obj2, ignoreKeys ){
    if ( obj1 == obj2 ){  return true;  }
    for ( key in obj1 ){
        if ( ignoreKeys.includes(key) ){  continue;  }
        if ( !(key in obj2) ){  return false;  }
        if ( obj1[key] != obj2[key] ){  return false;  }
    }
    for ( key in obj2 ){
        if ( ignoreKeys.includes(key) ){  continue;  }
        if ( !(key in obj1) ){  return false;  }
    }
    return true;
}



///////////////////////////////////////////////////////////////////////////////////////
// HTML construction

    function
htmlToElement( html ){
    var tempDiv = document.createElement('div');
    tempDiv.innerHTML = html;
    var element = ( tempDiv.children.length == 1 )?  tempDiv.children[0]  :  tempDiv;
    return element;
}

    function
applyIdSuffix( element, suffix ){
    if ( element.id ){  element.id = toId( element.id, suffix );  }

    // Point labels to correct html-element within same element-object
    if ( element.htmlFor ){  element.htmlFor = toId( element.htmlFor, suffix );  }

    var ariaControls = element.getAttribute ?  element.getAttribute('aria-controls')  :  null;
    if ( ariaControls ){  element.setAttribute( 'aria-controls', toId(ariaControls, suffix) );  }

    for ( var c = 0;  c < element.childNodes.length;  ++c ){
        applyIdSuffix( element.childNodes[c], suffix );
    }
}

    function
toId( idBase, idSuffix ){
    return idBase + '-' + idSuffix;
}

    function
setChildren( element, newChildren ){
    clearChildren( element );
    if ( newChildren ){
        for ( var c = 0;  c < newChildren.length;  ++c ){
            element.appendChild( newChildren[c] );
        }
    }
}

    function
moveChildren( oldParent, newParent ){
    while ( oldParent.firstChild ){
        newParent.appendChild( oldParent.firstChild );
    }
}

    function
clearChildren( element ){
    while ( element.firstChild ){
        element.removeChild( element.firstChild );
    }
}


///////////////////////////////////////////////////////////////////////////////////////
// Element wrapper class, for easy creating and updating html values.

    function
ElementWrap( ){ }

ElementWrap.prototype.createFromHtml = function( idSuffix, html ){
    this.element = htmlToElement( html );
    this.idSuffix = idSuffix;
    this.indexIds( this.element );
    this.attachHandlers( this.element );
    applyIdSuffix( this.element, this.idSuffix );  // Make IDs specific to this reason instance. 
    this.attachSubelements( this.element );  // Attach sub-elements last, so they do not get double-suffixed nor attach wrong handlers.
    return this.element;  // Return DOM element so that it can be added to webpage. 
};

ElementWrap.prototype.getId = function( idBase ){
    return toId( idBase, this.idSuffix );
};

ElementWrap.prototype.getSubElement = function( idBase ){
    var subelement = this.idBaseToElement ?  this.idBaseToElement[idBase]  :  null;
    if ( ! subelement ){  console.log('subelement=null for idBase=', idBase, ' this=', this);  }
    if ( ! subelement ){  throw new Error('subelement=null for idBase=' + idBase + ' this=' + this);  }
    return subelement;
};

// For convenience, and for efficiency to only set property if value changed.
ElementWrap.prototype.setProperty = function( subElementId, propName, value ){
    var subelement = this.getSubElement( subElementId );
    if ( subelement[propName] === value ){  return;  }
    if ( value === null  ||  value === undefined ){  delete subelement[propName];  }
    else {  subelement[propName] = value;  }
};

// Sets member variable that cannot be deleted
ElementWrap.prototype.setRequiredMember = function( subElementId, varName, value ){
    var subelement = this.getSubElement( subElementId );
    if ( subelement[varName] === value ){  
        return;  
    }
    else {  subelement[varName] = value;  }
};

ElementWrap.prototype.setAttribute = function( subElementId, attributeName, value ){
    var subelement = this.getSubElement( subElementId );
    if ( subelement.getAttribute( attributeName ) === value ){  return;  }
    if ( value ){  subelement.setAttribute( attributeName, value );  }
    else {  subelement.removeAttribute( attributeName );  }
};

ElementWrap.prototype.setStyle = function( subElementId, styleVarName, value ){
    var subelement = this.getSubElement( subElementId );
    if ( subelement.style[styleVarName] === value ){  return;  }
    if ( value ){  subelement.style[styleVarName] = value;  }
    else {  subelement.style[styleVarName] = null;  }
};

ElementWrap.prototype.setInnerHtml = function( subElementId, html ){
    var subelement = this.getSubElement( subElementId );
    if ( subelement.innerHTML === html ){  return;  }
    if ( html === undefined  ||  html === null ){  html = '';  }
    subelement.innerHTML = html;
};

ElementWrap.prototype.setClass = function( subElementId, className, isClassTrue ){
    var subelement = this.getSubElement( subElementId );
    if ( isClassTrue ){  subelement.classList.add( className );  }
    else {  subelement.classList.remove( className );  }
};

// Collect idBaseToElement : map[ subelement bare id -> subelement instance object ]
ElementWrap.prototype.indexIds = function( htmlElement, prefix ){
    // Collect subelement object and id
    if ( ! this.idBaseToElement ){  this.idBaseToElement = {};  }
    if ( htmlElement.id ){  this.idBaseToElement[ htmlElement.id ] = htmlElement;  }
    // Recurse on children
    for ( var c = 0;  c < htmlElement.children.length;  ++c ){
        this.indexIds( htmlElement.children[c], prefix + '    ' );
    }
};


// Replace element event-handler function names from literal HTML, with ElementWrap functions.
ElementWrap.prototype.attachHandlers = function( htmlElement ){

    var thisDisp = this;  // Copy for closure of handler functions created below.

    // For each event type... if DOM element specifies handler name... replace handler name with handler function from object.
    // for-loop over event names, creating callbacks, requires closure on handlerFunc.
    EVENT_NAMES.map(  function( eventName ){
        eventName = 'on' + eventName;
        var handlerName = htmlElement.getAttribute( eventName );
        if ( handlerName ){
            var handlerFunc = thisDisp[ handlerName ];  // Copy for closure of handler function created below.
            // Assign event handler to callback that assigns "this" to display.
            htmlElement[ eventName ] = function(event){
                handlerFunc.call(thisDisp, event);
            };
        }
    } );
    // Recurse on children.
    for ( var c = 0;  c < htmlElement.children.length;  ++c ){
        this.attachHandlers( htmlElement.children[c] );
    }
};

    
// Replace subdisplay tag with contained display-object
ElementWrap.prototype.attachSubelements = function( htmlElement ){
    var subdisplayName = htmlElement.getAttribute('subdisplay');
    if ( subdisplayName ){
        var subdisplay = this[ subdisplayName ];
        htmlElement.appendChild( subdisplay.element );
    }
    // Recurse on children.
    for ( var c = 0;  c < htmlElement.children.length;  ++c ){
        this.attachSubelements( htmlElement.children[c] );
    }
};

ElementWrap.prototype.dataUpdated = null;  // Abstract method



///////////////////////////////////////////////////////////////////////////////////////
// Transitory message display

const MESSAGE_TRANSITION_MS = 2000;  // Match CSS for role=alert

// Returns updated value of struct 
    function
showMessageStruct( struct, div ){
    if ( struct ){
        showMessage( struct.text, struct.color, struct.ms, div );
    }
    return null;
}

    function
showMessage( text, color, disappearMs, element ){

    stopMessageTimer( element );
    
    // If new message is unchanged... do nothing
    if ( element.innerHTML == text ){  return;  }

    // If new text is empty... hide message
    if ( ! text ){  hideMessage( element );  return;  }

    // If old text was empty... start message as hidden
    var elementJquery = jQuery( element );
    var wasHidden = isHidden( element );
    if ( wasHidden ){
        elementJquery.hide();
    }
    
    // Set text
    element.innerHTML = text;
    element.style.color = color;

    // Show message
    wasHidden |= elementJquery.is(':hidden');
    if ( wasHidden ){  elementJquery.slideToggle( MESSAGE_TRANSITION_MS / 4 );  }  // Slide before fade-in
    element.style.opacity = 1.0;  // Requires MESSAGE_TRANSITION_MS
    element.style.visibility = 'visible';

    // Start to hide message after delay.  Store timer in html-element itself, to ensure 1-to-1 relation.
    if ( disappearMs ){
        element.hideTimer = setTimeout( function(){ 
            hideMessage(element); 
        } , disappearMs );
    }
}

    function
hideMessage( element ){
    stopMessageTimer( element );
    if ( isHidden( element ) ){  return;  }

    // Start transition
    element.style.opacity = 0.0;  // Requires MESSAGE_TRANSITION_MS
    var elementJquery = jQuery( element );
    elementJquery.slideToggle( MESSAGE_TRANSITION_MS );
    // Finish hiding message after transition.  Store timer in html-element, to ensure 1-to-1 relation.
    element.hideTimer = setTimeout( function(){
        element.style.visibility = 'hidden';  // So that screen readers do not read empty alert
        element.innerHTML = '';
    } , MESSAGE_TRANSITION_MS );
}

    function
isHidden( element ){  
    return ( ! element.innerHTML  ||  element.style.visibility == 'hidden' );  
}

    function
stopMessageTimer( element ){
    // Stop existing timer stored in element
    if ( element.hideTimer ){
        clearTimeout( element.hideTimer );
        element.hideTimer = null;
    }
}

    function
defaultTo( value, defaultValue ){  return value ? value : defaultValue;  }

// Prevents multiple delayed-calls to f()
// Stores f() delayed-call handle, inside f() itself.
    function
deduplicate( delayMs, obj, f ){
    if ( f.deduplicateTimer ){
        clearTimeout( f.deduplicateTimer );
        f.deduplicateTimer = null;
    }
    f.deduplicateTimer = setTimeout( f.bind(obj) , delayMs );
}



///////////////////////////////////////////////////////////////////////////////////////
// Focus and traversal

// Make ENTER key activate links and buttons
    function
enterToClick( event ){
    if( event.key == KEY_NAME_ENTER ){  event.currentTarget.click();  }
}

    function
containsFocus( containingElement ){
    for ( var ancestor = document.activeElement;  ancestor != null;  ancestor = ancestor.parentElement ){
        if ( ancestor == containingElement ){  return true;  }
    }
    return false;
}

    function
focusNextTabStop( currentElement ){
    // Scan forward to next HTML element with tabstop >= 0
    for ( var e = nextElementOutside( currentElement );  e != null;  e = nextElement(e) ){
        if ( e.tabIndex !== undefined  &&  e.tabIndex !== null  &&  e.tabIndex >= 0 ){
            e.focus();
            return;
        }
    }
}

    function
nextElement( element ){
    if ( ! element ){  return null;  }
    // If element has children... return first child 
    if ( element.children  &&  element.children.length > 0 ){  return element.children[0];  }
    return nextElementOutside( element );
}

    function
nextElementOutside( element ){
    // For each ancestor, starting from element... if ancestor has next sibling... return sibling 
    for ( var ancestor = element;  ancestor != null;  ancestor = ancestor.parentElement ){
        if ( ancestor.nextElementSibling ){
            return ancestor.nextElementSibling;
        }
    }
    return null;
}



///////////////////////////////////////////////////////////////////////////////////////
// AJAX

    function
ajaxPost( sendData, url, callback, synchronous ){
    // callback:f(error, status, responseData)

    jQuery.ajax( {
        accepts: 'application/json' , 
        async: !synchronous ,
        contentType: 'application/json' , 
        data: JSON.stringify(sendData) ,
        dataType: 'json' ,
        error: function(request, status, error){ 
            // nodeJs/Express can return error code + JSON, but jQuery will discard the JSON data.
            var responseData = null;
            try {  responseData = JSON.parse( request.responseText );  } catch(e){  }
            callback(error, status, responseData); 
            } ,
        method: 'POST' ,
        success: function(responseData, status, request){
            if ( responseData ){  callback(null, status, responseData);  }
            else {  callback('data response failed', status, responseData);  }
        } ,
        url: url
    } );

    return false;
}


    function
ajaxGet( sendData, url, callback ){
    // callback:f(error, status, responseData)
    
    const useAjaxFileForTest = false;

    jQuery.ajax( {
        accepts: 'application/json' , 
        async: true ,
        cache: false ,
        data: sendData ,
        dataType: 'json' ,
        error: function(request, status, error){
            // nodeJs/Express can return error code + JSON, but jQuery will discard the JSON data.
            var responseData = null;
            try {  responseData = JSON.parse( request.responseText );  }  catch(e){  }
            callback(error, status, responseData);
        } ,
        method: 'GET' ,
        beforeSend:  useAjaxFileForTest ?  function(xhr){ xhr.overrideMimeType('application/json'); }  :  undefined ,
        success: function(responseData, status, request){
            if ( responseData ){  callback(null, status, responseData);  }
            else {  callback('data response failed', status, responseData);  }
        } ,
        url: url
    } );
    return false;
}


///////////////////////////////////////////////////////////////////////////////////////
// Login

// Cookies-required dialog buttons
elementWithId('cookiesRequiredDiv').onclick = function(event){
    if ( ! $(event.target).parents('.modalPopupDiv').length ){ hide('cookiesRequiredDiv'); uncheckLoginRequired(); }  
};
elementWithId('cookiesCancelButton').onclick = function(){ hide('cookiesRequiredDiv'); uncheckLoginRequired(); };

// Login-required dialog buttons
elementWithId('loginRequiredDiv').onclick = function(event){  
    if ( ! $(event.target).parents('.modalPopupDiv').length ){ hide('loginRequiredDiv'); uncheckLoginRequired(); }  
};
elementWithId('loginCancelButton').onclick = function(){ hide('loginRequiredDiv'); uncheckLoginRequired(); };
elementWithId('loginButton').onclick = function(){  return openLoginPage(); };

// Logout dialog buttons
elementWithId('logoutDiv').onclick = function(event){
    if ( ! $(event.target).parents('.modalPopupDiv').length ){ hide('logoutDiv'); }  
};
elementWithId('logoutCancelButton').onclick = function(){ hide('logoutDiv') };
elementWithId('logoutButton').onclick = function(){  requestLogout( onLoggedOut )  };

// Login menu buttons
document.getElementById('menuItemLogin').onclick = requireLogin;
document.getElementById('menuItemLogout').onclick = function(){  
    document.getElementById('logoutDiv').setAttribute( 'show', null );  
    elementWithId('logoutCancelButton').focus();
};

    function
uncheckLoginRequired(){
    var loginRequiredCheckbox = elementWithId('loginRequiredCheckbox');
    if ( loginRequiredCheckbox ){  loginRequiredCheckbox.checked = false;  }
}



    function
requireLogin( ){
    // Returns loggedIn:boolean
    // Optional callback:f( loggedIn:boolean )
    
    // If login-cookie does not exist...
    //     Pop up login-required dialog, which opens login-tab, retrieves login-request-id & signature, posts to login-site.
    //     When login-site succeeds, login-tab redirects to calling site, and calling site sets login-cookie.
    //     When login-tab disappears & page re-focuses, dismiss login-required dialog, retrieve login-crumb.

    // If browser cookie is not set... show cookies-required dialog
    var cookiesRequiredDiv = document.getElementById('cookiesRequiredDiv');
    if ( document.cookie ){ 
        cookiesRequiredDiv.setAttribute( 'show', 'false' );
    }
    else {
        cookiesRequiredDiv.setAttribute( 'show', null );
        document.getElementById('cookiesCancelButton').focus();
        return false;
    }

    // If not logged in... show login-dialog
    if ( ! haveLoginCookie() ){
        showLoggedOutControls();
        elementWithId('loginRequiredDiv').setAttribute('show', null);
        elementWithId('loginButton').focus();
    }

    return true;
}



    function
openLoginPage( ){

    // Server generates login-request-key, signs login-request using app-secret
    // Because Safari only allows new tab/window from within button onclick={return true} function ...
    //     run AJAX synchronously to retrieve login-request-signature.
    // Alternatively... if browser blocks form submit to new tab via form.submit() ... 
    //     AJAX-retrieve signature before showing dialog, then use login-button to submit to new tab, without javascript.
    //         Risk of undetectable signature timeout before user completes login.
    //             Refresh signature with page refocus + client-side timer?
    //     Or... immediately show dialog, with login-button disabled until signature retrieved async

    var ajaxSync = true;
    var ajaxSuccess = false;
    ajaxPost( {crumb2:crumb}, 'signLoginRequest', function(error, status, responseData){

        if ( error  ||  !responseData.success  ||  ! responseData.signature  ||  ! responseData.loginRequestId ){  return;  }

        // In a new tab, post data to voter-login service
        document.getElementById('inputSignature').value = responseData.signature;
        document.getElementById('requestId').value = responseData.loginRequestId;
        ajaxSuccess = true;
    } , ajaxSync );
    
    return ajaxSuccess;
}



    function
updateWaitingLogin( callback ){
    // Called on page-focus, to dismiss login-dialog, and try to retrieve login crumb 
    // Runs callback when logged in 

    // If have login-cookie... dismiss login-dialog, run callback 
    if ( haveLoginCookie()  &&  crumbForLogin ){
        updateLoginDialog();
        if ( callback ){  callback();  }
    }
    // If need login-cookie/crumb... try to retrieve 
    else if ( showingLoginDialog() ){
        retrieveLogin( function(error, success){
            updateLoginDialog();
            if ( callback ){  callback();  }
        } );
    }
    // If login not required... run callback 
    else {
        updateLoginDialog();
        if ( callback ){  callback();  }
    }
}

    function
showingLoginDialog( ){
    var loginRequiredDiv = elementWithId('loginRequiredDiv');
    var show = loginRequiredDiv.getAttribute('show');
    return (show != 'false');
}



    function
updateLoginDialog( ){
    // Will show/hide dialog, but will not try to retrieve login data
    if ( haveLoginCookie() ){  showLoggedInControls();  }
    else                    {  showLoggedOutControls();  }
}

    function
showLoggedInControls( ){
    elementWithId('loginRequiredDiv').setAttribute('show', 'false');
    elementWithId('menuItemLogin').setAttribute('show', 'false');
    elementWithId('menuItemLogout').setAttribute('show', null);

    var city = loginCity();
    elementWithId('menuItemCity').innerHTML = city;
    elementWithId('menuItemCity').setAttribute( 'show' , (city ? null : 'false') );
}

    function
showLoggedOutControls( requireLogin ){
    elementWithId('menuItemLogin').setAttribute('show', null);
    elementWithId('menuItemLogout').setAttribute('show', 'false');

    elementWithId('menuItemCity').setAttribute('show', 'false');
}



    function
retrieveLogin( callback ){
    // callback:f( error, success:boolean )
    ajaxGet( {}, 'getLogin', function(error, status, responseData){
        var success = ( ! error  &&  responseData  &&  responseData.success );
        if ( success ){
            crumbForLogin = responseData['crumbForLogin'];
        }
        callback( error, success );
    } );
}

    function
loginCity( ){
    var cookieData = parseCookie();
    if ( ! cookieData ){  return null;  }
    var city = cookieData['city'];
    return city ?  city  :  null;
}

    function
haveLoginCookie( ){
    var cookieData = parseCookie();
    return ( cookieData  &&  cookieData['hasVoterId'] );
}

// Returns data-structure or null
    function
parseCookie( ){
    // For each cookie...
    var cookies = document.cookie.split(';');
    for ( var c = 0;  c < cookies.length;  ++c ){
        var cookie = cookies[c];
        // Parse cookie base-64-encoded JSON
        var cookieNameAndValue = cookie.split('=');
        var cookieName = cookieNameAndValue[0];
        cookieName =  cookieName ?  cookieName.trim()  :  null;
        var cookieValue = cookieNameAndValue[1];
        if ( cookieName != 'J' ){  continue;  }
        var cookieValue64 = cookieValue.replace( /"/g, '' ).replace( /\\075/g , '=' );
        var cookieValueJson = atob( cookieValue64 )
        var cookieData = ( cookieValueJson )?  JSON.parse( cookieValueJson )  :  null;
        return cookieData;
    }
}

    function
requestLogout( callback ){
    // Requests logout
    // Runs callback when logged out
    var sendData = { crumb:crumb , crumbForLogin:crumbForLogin };
    ajaxPost( sendData, 'submitLogout', function(error, status, responseData){
        var success = (  !error  &&  responseData  &&  ( responseData.success || responseData.message == NO_LOGIN )  );
        if ( success ){  callback();  }
    } );
}

    function
onLoggedOut( ){
    hide('logoutDiv');
    updateLoginDialog();
    crumbForLogin = null;
}

    function
hide( elementId ){
    elementWithId( elementId ).setAttribute( 'show', 'false' );
}




///////////////////////////////////////////////////////////////////////////////////////
// Highlighting spans

    function 
unique( arrayValues ){ 
    var valueSet = { }; 
    for ( var i = 0;  i < arrayValues.length;  ++i ){  valueSet[ arrayValues[i] ] = true;  } 
    uniqueValues = [ ]; 
    for ( value in valueSet ){  uniqueValues.push( value );  } 
    return uniqueValues; 
} 

    function
keywordsToHighlightSpans( keywordsString, text ){
    var intervals = keywordMatchIntervals( keywordsString, text );
    return intervalsToHighlightSpans( intervals, text );
}

    function
intervalsToHighlightSpans( intervals, text ){
    var spans = [];
    for ( var i = 0;  i < intervals.length;  ++i ){
        var interval = intervals[i];
        var matchText = text.substring( interval.start, interval.end );
        var spanClass = ( interval.match )? 'Highlight' : null;
        spans.push(  makeSpan( spanClass, matchText )  );
    }
    return spans;
}

    function
makeSpan( className, innerText ){ 
    var span = document.createElement('span'); 
    if ( className ){  span.classList.add( className );  }
    span.innerHTML = innerText;
    return span;
}

    function
keywordMatchIntervals( keywordsString, text ){

    var intervals = [];

    // Collect matching words, dropping suffixes
    // Ignore case, stop-words, suffixes ("ed", "s", "ing")
    // Include whitespace between matched words
    var keywordsArray = tokenize( keywordsString );

    var keywordStems = keywordsArray.map( function(w){ return w.replace( /(s|ed|ing)$/ , '' ); } )
    keywordStems = unique( keywordStems );
    
    keywordsFiltered = keywordStems.filter(  function(w){ return (w != '') && !(w in STOP_WORDS); }  );

    // Construct regex to match answer input word sequences, with filtering and stemming
    var stemsRegexText = keywordsFiltered.join('|');
    var wordsRegexText = '\\b(' + stemsRegexText + ')(s|ed|ing|)\\b';  // Require word boundaries around match

    var wordSeqRegex = new RegExp(  '(' + wordsRegexText + '\\s*)+' , 'ig'  );  // Highlight a sequence of words with space between

    // Loop, for each match, with limit because some regex may match everything ...
    var lastMatchEnd = 0;
    var maxLoops = 30;
    for ( var match = true;  maxLoops > 0  &&   match;  --maxLoops ){
        // Find matching word sequence
        wordSeqRegex.lastIndex = lastMatchEnd;
        match = ( stemsRegexText == '' ) ?  false  :  wordSeqRegex.exec( text );
    
        // Append preceding non-matching span
        var nonMatchingEnd = ( match )?  match.index  :  text.length;
        intervals.push( {start:lastMatchEnd, end:nonMatchingEnd, match:false} );

        // Append collected matching span
        if ( match ){
            lastMatchEnd = match.index + match[0].length;
            intervals.push( {start:match.index, end:lastMatchEnd, match:true} );
        }
    }
    if (maxLoops <= 0){  console.error( 'maxLoops=0' );  }
    
    return intervals;
}

    function
tokenize( text ){
    if ( ! text ){  return [];  }
    return text.toLowerCase().split( /[^a-z0-9\-]+/ );
}



///////////////////////////////////////////////////////////////////////////////////////
// Statistics

    function 
incrementMapValue( map, key, increment ){
    var oldCount = map[ key ];
    var newCount = ( oldCount )?  oldCount + increment  :  increment;
    map[ key ] = newCount;
    return newCount;
}


