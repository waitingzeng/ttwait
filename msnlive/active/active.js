
var email = '';
if (phantom.args.length === 0) {
    phantom.exit()
} else {
    email = phantom.args[0];
}
var webpage = require('webpage');
var page = null;

phantom.injectJs('log.js');
var log = open_log('active_js', '/root/data/log');
log.open_debug();

var active = function(email){
    page = require('webpage').create();
    page.lastload = Date.now()
    page.onConsoleMessage = function(msg){log.info(email + ' ' + msg);};
    log.info("begin active " + email); 
    var res_func = function(ret){ 
        log.info(" ret is " + ret);
        phantom.exit(ret);
        return ret;
    }
    

    var t = setInterval(function(){
        if(!page) clearInterval(t);
        if(!page.lastload)return;
        var t = Date.now() - page.lastload;
        //console.log("the page timeout " + t);
        if(t > 60000 ){
            clearInterval(t);
            return res_func(3);
            
        }
    }, 2000);


    page.open('https://profile.live.com', function (status) {
        page.lastload = Date.now();
        if (status !== 'success') {
            log.info( email + ' fail');
            return res_func(1);
        } else {
            var url = page.evaluate(function(){
	            return document.location.href;
	        });
	        log.info('load ' + url + ' finish');
            page.injectJs('jquery.min.js');
	        if(url.indexOf('https://login.live.com/login.srf') == 0){
		        page.evaluate(function (email) {
		            $jq('#i0116').val(email);
		            $jq('#i0118').val('846266');
	                $jq('#idSIButton9').click();
	
		        }, email);
	        } else if (url.indexOf('https://profile.live.com/P.mvc#!/cid-') == 0) {
	            console.log('active success');
                return res_func(0);
                
	        } else if(url.indexOf('https://account.live.com/Logincredprof.aspx') == 0){
	            page.evaluate(function(){
		            $jq('#iCurPassword').val('846266').blur();
		            $jq('#ctl00_ctl00_MainContent_MainContent_AccountContent_LoginWrapper_LoginRepeater_ctl00_LoginOther_Question').get(0).selectedIndex = 1;
		            $jq('#ctl00_ctl00_MainContent_MainContent_AccountContent_LoginWrapper_LoginRepeater_ctl00_LoginOther_iSecretAnswer').val('最少 5 个字符');
		            $jq('#ctl00_ctl00_MainContent_MainContent_AccountContent_btSubmit').click();
	                
	            });
	        } else if(url.indexOf('https://account.live.com/Proofs/Manage') == 0 || url.indexOf('https://account.live.com/proofs/Manage') == 0){
                
	            page.evaluate(function(email){
                    if($jq('#DoneBtn').css('display') == 'none'){
                        $jq('#EmailAddress').val(email.replace('@', '_').replace('.', '_') + '@yeah.net');
                        $jq('#SaveBtn').click();
                    }else{
                        $jq('#DoneBtn').click();
                    }
	                
	            }, email);
	        } else if (url.indexOf('https://account.live.com/security/Sai.aspx/A1') == 0){
                return res_func(2);
	        }
	
	    }
	    //phantom.exit();
	});
}

ret = active(phantom.args[0]);

