
var email = '';
    console.log('args' + JSON.stringify(phantom.args));
    email = phantom.args[0];
    name = phantom.args[1];
var page = new WebPage();
page.onConsoleMessage = function(msg){console.log(msg);};
//page.onResourceRequested = function(request)
//{
//    console.log('Request ' + request.url);//JSON.stringify(request, undefined, 4));
//};

function evaluate(page, func) {
    var args = [].slice.call(arguments, 2);
    var fn = "function() { return (" + func.toString() + ").apply(this, " + JSON.stringify(args) + ");}";
    return page.evaluate(fn);
}
    
page.open('https://profile.live.com', function (status) {
    if (status !== 'success') {
        console.log(name + ' ' + email + ' fail');
        phantom.exit(1);
    } else {
        var url = page.evaluate(function(){
            return document.location.href;
        });
        console.log(name + ' ' + email + ' ' + url);
        if(url.indexOf('https://login.live.com/login.srf') == 0){
            page.injectJs('jquery.min.js');
            console.log('inject jquery' + email);
	        evaluate(page, function (email) {
	            $('#i0116').val(email);

	            $('#i0118').val('846266');
                console.log('bbba' + email)
                $('#idSIButton9').click();

	        }, email);
        } else if (url.indexOf('https://profile.live.com/P.mvc#!/cid-') == 0) {
            console.log(name + ' ' + email + ' success');
            phantom.exit(0);
        } else if(url.indexOf('https://account.live.com/Logincredprof.aspx') == 0){
            //page.injectJs('jquery.min.js');
            page.evaluate(function(){
	            var $ = jQuery;
	            $('#iCurPassword').val('846266').blur();
	            $('#ctl00_ctl00_MainContent_MainContent_AccountContent_LoginWrapper_LoginRepeater_ctl00_LoginOther_Question').get(0).selectedIndex = 1;
	            $('#ctl00_ctl00_MainContent_MainContent_AccountContent_LoginWrapper_LoginRepeater_ctl00_LoginOther_iSecretAnswer').val('最少 5 个字符');
	            $('#ctl00_ctl00_MainContent_MainContent_AccountContent_btSubmit').click();
                
            });
        } else if(url.indexOf('https://account.live.com/Proofs/Manage') == 0){
            page.evaluate(function(email){
                var $ = jQuery;
                //$('#EmailAddress').val(email.replace('@', '_').replace('.', '_') + '@yeah.net');
                $('#SaveBtn').click();
            }, email);
        } else if (url.indexOf('https://account.live.com/security/Sai.aspx/A1') == 0){
            phantom.exit(2);
        }

    }
    //phantom.exit();
});
