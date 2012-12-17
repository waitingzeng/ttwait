
if (phantom.args.length != 2) {
    phantom.exit();
} else {
    uin = phantom.args[0];
    psw = phantom.args[1];
}

phantom.injectJs('jscomm/lib.js');

injectjs(phantom);

var log = open_log('weixin');
log.open_debug()
fs = require('fs');


var page = get_page();
var url = 'http://ui.ptlogin2.paipai.com/cgi-bin/login?appid=17000101&style=0&target=self&no_verifyimg=1&hide_title_bar=1&f_url=loginerroralert&bgcolor=f2faff&link_target=blank&s_url=http://member.paipai.com/cgi-bin/ptlogin%3Floginfrom%3D18';

page.open(url, function(status){
    
    if (status != 'success') {
        log.info('{0} open fail', url);
        phantom.exit();
    } else {
        url = page.evaluate(function(){
            return document.location.href;
        });
    }

    log.info('{0} open success', url);
    
    injectjs(page);

    if(url.indexOf('http://ui.ptlogin2.paipai.com/') == 0){
        page.evaluate(function (uin, psw) {
            setTimeout(function(){
                //console.log("isAbleSubmit : " + isAbleSubmit);
                $jq('#u').val(uin).blur();
                
                setTimeout(function(){
                    $jq('#p').val(psw).blur();
                    setTimeout(function(){
                        $jq('#login_button').click();
                    }, 2000)
                }, 2000)

            }, 1000);
            
        }, uin, psw);
    }else if(url.indexOf('http://ptlogin2.paipai.com/login') == 0){
        var content = page.evaluate(function(){
            return document.body.innerText;
        });
        log.info('response content {0}', content);
    }else if(url.indexOf('http://member.paipai.com/') == 0){
        
        var cookie = page.evaluate(function(){
            return document.cookie;
        });
        cookie_file = fs.open($jq.format('/tmp/{0}_paipai_cookie', uin), 'w');
        cookie_file.write(cookie);
        cookie_file.close();
        log.info('login success, save cookie ' + cookie);
        phantom.exit();
    }
    else{
        log.info('{0} not process', url);
    }

});

