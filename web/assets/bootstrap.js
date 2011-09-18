var monitorify = (function($){
    $this = this;
    $this.context = {region:'all', type:'all', name:'all', from_date:'', to_date:''};
    $this.filters = {};

    // Helper functions
    $this.h = {
        d: function(i){return(new Date(i*(i>2000000000?1:1000)));},
        base: function(str, from, to) {var SYMBOLS = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"; var i, nbaseten=0; if (from!=10) {var sizestr = str.length; for (i=0; i<sizestr; i++) {var mul, mul_ok=-1; for (mul=0; mul<SYMBOLS.length; mul++) {if (str[i]==SYMBOLS[mul]) {mul_ok = 1; break;}} var exp = (sizestr-i-1); if (exp==0) {nbaseten += mul;} else {nbaseten += mul*Math.pow(from, exp);}}} else {nbaseten = parseInt(str);} if (to!=10) {var nto = []; while (nbaseten>0) {var mod = nbaseten%to; nto.push(SYMBOLS[mod]); nbaseten = parseInt(nbaseten/to);} return nto.reverse().toString().replace(/,/g, '');} else {return nbaseten.toString();}},
        enc: function(s){return($this.h.base(new Number(s), 10, 62));},
        dec: function(s){return($this.h.base(new Number(s), 62, 10));},
        url: function(){
            var url = [];
            url.push(encodeURIComponent($this.context.type));
            url.push(encodeURIComponent($this.context.region));
            url.push(encodeURIComponent($this.context.name));
            if($this.context.to_date){
                url.push($this.h.enc($this.context.from_date) + '-' + $this.h.enc($this.context.to_date));
            } else {
                url.push($this.h.enc($this.context.from_date));
            }
            return('/' + url.join('/'));
        }
    }

    // Methods
    $this.loadContext = function(){
        var a = location.pathname.substring(1).split('/');
        var newContext = {};
        if(a.length>=1) newContext['type'] = a[0];
        if(a.length>=2) newContext['region'] = a[1];
        if(a.length>=3) newContext['name'] = a[2];
        if(a.length>=4) {
            var d = newContext['type'].split('-');
            if(d.length>=1) newContext['from_date'] = $this.h.dec(d[0]);
            if(d.length>=2) newContext['to_date'] = $this.h.dec(d[1]);
            if(typeof(newContext['to_date'])=='undefined' || newContext['to_date']=='' || newContext['to_date']<=0) 
                newContext['to_date'] = (new Date())*1;
            if(typeof(newContext['from_date'])=='undefined' || newContext['from_date']=='' || newContext['from_date']<=0) 
                newContext['from_date'] = newContext['to_date'] - (1000*60*60*24*7);
        }
        $this.switchContext(newContext, true);
    }
    $this.loadFilters = function(){
        $.ajax({
            url: "/api/filters",
            success: function(filters){
                $this.filters = filters;
            }
        });
    };
    $this.updateCharts = function(){
        $.ajax({
            url: "/api/data",
            data:$this.context,
            success: function(data){
            }
        });
    };
    $this.switchContext = function(delta, replace){
        $.each(delta, function(k,v){
            $this.context[k] = v;
        });
        var url = $this.h.url();
        var title = 'Monitorify';
        if(typeof(replace)!=='undefined' && replace) {
            History.replaceState($this.context, title, url);
        } else {
            History.pushState($this.context, title, url);
        }
    }
    
    // Hook to History.js
    History.Adapter.bind(window, 'statechange', function(){
        var State = History.getState();
        console.debug(State.data, State.title, State.url);
        $this.updateCharts();
    });

    // Initialize
    $this.loadContext();
    $this.loadFilters();
    return(this);
}(jQuery));
