import execjs

ctx = execjs.compile("""
            function $time33(str){
                for(var i=0,len=str.length,hash=5381;i<len;++i){
                    hash+=(hash<<5)+str.charAt(i).charCodeAt();
                };
                return hash&0x7fffffff;
            }
            """)

print ctx.call('$time33', 'aaaa')


def time33(s):
    hash = 5381
    l = len(s)
    for x in s:
        hash += (hash << 5) + ord(x)
    return hash & 0x7fffffff

print time33('aaaa')

if __name__ == '__main__':
    time33('aaaa')
