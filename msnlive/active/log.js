
phantom.injectJs("date.js");

fs = require('fs');
function open_log(name, path){
    
    var _root = path;
    var _cur_file = null;
    var _cur_name = null;
    var _debug = false;

    var get_cur_name = function(){
        var cur = new Date();
        return _root + cur.Format('/MMddhh.log');
    }
    var open = function(){
        if(!_cur_file){
            _cur_name = get_cur_name();
            _cur_file = fs.open(_cur_name, 'a');
        }else{
            new_name = get_cur_name();
            if(_cur_name != new_name){
                _cur_file.close();
                _cur_name = new_name;
                _cur_file = fs.open(_cur_name, 'a');
            }
        }
    }
    var write = function(s){
        open();
        var date = new Date();
        var prefix = name + date.Format(' <hh:mm:ss> ')
        //console.log(_cur_name);
        if(_debug){
            console.log(prefix + s);
        }
        _cur_file.write(prefix + s + '\n');
        _cur_file.flush();
    }
    var log = {
       info : function(s){
           write(s);       
       },
       open_debug : function(){
           _debug = true;                
       }
    }
    return log;
}
