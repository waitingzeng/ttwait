
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
log.open_debug()
//log.open_debug();
console.log = log.info
var dumps = function(email){
    page = require('webpage').create();
    page.lastload = Date.now()
    page.onConsoleMessage = function(msg){log.info(email + ' ' + msg);};
    log.info("begin dumps " + email); 
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
        if(t > 20000 ){
            clearInterval(t);
            return res_func(3);
            
        }
    }, 2000);


    page.open('https://mail.live.com/default.aspx?rru=contacts', function (status) {
        page.lastload = Date.now();
        if (status !== 'success') {
            log.info( email + ' fail status ' + status);
            return res_func(1);
        } else {
            var url = page.evaluate(function(){
	            return document.location.href;
	        });
	        log.info(url);
	        if(url.indexOf('https://login.live.com/login.srf') == 0){
                if(page.content.indexOf('rd()') > 0){
                    log.info('redirect to rd');
                    page.evaluate(function () {

                        window.location.href = 'https://mail.live.com/mail/GetContacts.aspx?n=' + Math.random();
                        console.log(window.location.href)
                    });
                }else{
    	            page.injectJs('jquery.min.js');
    		        page.evaluate(function (email) {
    		            $('#i0116').val(email);
    		            $('#i0118').val('846266');
    	                $('#idSIButton9').click();
    	
    		        }, email);
                }
	        } else if (url.indexOf('https://account.live.com/security/Sai.aspx/A1') == 0){
                page.evaluate(function () {
                    location.href = 'https://mail.live.com/';
                })
	        } else if(url.indexOf('GetContacts.aspx') > 0){
                log.info(page.content);
                return res_func(0);
            }
	
	    }
	    //phantom.exit();
	});
}

ret = dumps(phantom.args[0]);

