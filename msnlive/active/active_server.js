
var system = require('system');
var webpage = require('webpage');
var server = require('webserver').create();
var port = 9000;
if(phantom.args.length == 1){
    port += parseInt(phantom.args[0]);
}
var page = null;
var active = function(email, response){
    page = require('webpage').create();
    page.lastload = Date.now()
    page.onConsoleMessage = function(msg){console.log('server ' + port + ' ' + msg);};
    console.log("begin active " + email); 
    var res_func = function(ret){ 
        if(response){
            response.statusCode = 200;
            response.headers = {"Cache": "no-cache", "Content-Type": "text/text"};
            // note: writeBody can be called multiple times
            response.write(ret);
            response.close();
            //page.release();
        }
        console.log("ret is " + ret);
        phantom.exit();
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


    page.open('https://profile.live.com', function (status) {
        page.lastload = Date.now();
        if (status !== 'success') {
            console.log(name + ' ' + email + ' fail');
            return res_func(1);
        } else {
            var url = page.evaluate(function(){
	            return document.location.href;
	        });
	        console.log('server ' + email + ' ' + url);
	        if(url.indexOf('https://login.live.com/login.srf') == 0){
	            page.injectJs('jquery.min.js');
		        page.evaluate(function (email) {
		            $('#i0116').val(email);
		            $('#i0118').val('846266');
	                $('#idSIButton9').click();
	
		        }, email);
	        } else if (url.indexOf('https://profile.live.com/P.mvc#!/cid-') == 0) {
	            console.log(name + ' ' + email + ' success');
                return res_func(0);
                
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
                return res_func(2);
	        }
	
	    }
	    //phantom.exit();
	});
}

//ret = active(phantom.args[0], null);


var listening = server.listen(port, function (request, response) {
    console.log("GOT HTTP REQUEST");
    //console.log(JSON.stringify(request, null, 4));
    email = request.url.split('email=')[1];

    ret = active(email, response);    

    // we set the headers here
});

if(!listening){
    console.log("start server fail " + port);
    phantom.exit();
}else{
    console.log("server start on " + port);
}

