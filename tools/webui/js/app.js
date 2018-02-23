var store;
var storeid;
var store_root;
var store_home;


var astore;
var dstore;
var aroot;
var droot;
var ahome;
var dhome;
var astoreid
var dstoreid

if (!library)
   var library = {};

library.json = {
   replacer: function(match, pIndent, pKey, pVal, pEnd) {
      var key = '<span class=json-key>';
      var val = '<span class=json-value>';
      var str = '<span class=json-string>';
      var r = pIndent || '';
      if (pKey)
         r = r + key + pKey.replace(/[": ]/g, '') + '</span>: ';
      if (pVal)
         r = r + (pVal[0] == '"' ? str : val) + pVal + '</span>';
      return r + (pEnd || '');
      },
   prettyPrint: function(obj) {
      var jsonLine = /^( *)("[\w]+": )?("[^"]*"|[\w.+-]*)?([,[{])?$/mg;
      return JSON.stringify(obj, null, 3)
         .replace(/&/g, '&amp;').replace(/\\"/g, '&quot;')
         .replace(/</g, '&lt;').replace(/>/g, '&gt;')
         .replace(jsonLine, library.json.replacer);
      }
   };


var wsconnect = function wsconnect() {

    //var rootString = document.getElementById('root').value;
    //if (rootString == "")
    //{
    //    //alert('Please enter a value for "Root"');
    //}
    //else
    //{
    display();
    //var rootString = document.getElementById('root').value;
    //var storeid = document.getElementById('storeid').value;
    // ws://139.162.144.10:9669/a1b2c3d4
    var host = 'ws://'+document.getElementById('connect').value+':9669/a1b2c3d4';
    //store_root = rootString;
    //store_home = rootString+'/web';

    aroot = 'afos://0';
    ahome = aroot+'/web';
    astoreid = 'aweb';

    droot = 'dfos://0';
    dhome = droot + '/web';
    dstoreid = 'dweb';


    document.getElementById('keyForm').value = droot;
    var fos = this.fog05;
    var art = new fos.Runtime(host);
    var drt = new fos.Runtime(host);

    art.onconnect = function () {
        astore = new fos.Store(art, astoreid, aroot, ahome, 1024);
    };

    drt.onconnect = function () {
        dstore = new fos.Store(drt, dstoreid, droot, dhome, 1024);
        refresh();
    };

    art.connect();
    drt.connect();

    setInterval(function(){refresh();}, 5000);
    setInterval(function(){refreshpage();}, 5000);
    //}
}

function pushKeyValue()
{
    var rootName = document.getElementById('root').value;
    var keyElem = document.getElementById('keyForm').value;
    var valueElem = document.getElementById('valueForm').value;
    var radioElem = radio();
    var selectElem = select();
    if (keyElem  == "")
    {
        alert('Please enter a value for "Key"');
    }
    else
    {
        if (selectElem == "put")
        {
            if (keyElem === rootName)
            {
                alert('Please enter a different key from the root');
            }
            else
            {
                store.put(keyElem, valueElem);
            }
        }
    }
}


var display = function display() {
    var page_connect = document.querySelectorAll('.page-connect.active');
    for (var i = 0; i < page_connect.length; i++)
    {
        page_connect[i].classList.remove('active');
    }

    var page_principal = document.querySelectorAll('.page-principal');
    for (var i = 0; i < page_principal.length; i++)
    {
        page_principal[i].classList.add('active');
    }
}

function refresh()
{
    refreshatree()
    refreshdtree()
}

function refreshatree()
{
    $(function () {
        $('#jstree').jstree(
            {
                "core" : {
                    check_callback : true,
                    "themes" : { "icons": true }
                }
            });

        $('#jstree').on('changed.jstree', function (e, data) {
            var i, j, r = [];
            for(i = 0, j = data.selected.length; i < j; i++) {
                r.push(data.instance.get_node(data.selected[i]).id);
            }
            var node = $('#jstree').jstree().get_node(r);
            astore.get(node.id, function(k, v) {
                document.getElementById("main").style.display = "block";
                console.log(`Key ${k}`)
                console.log(`Value ${v.value}`)
                console.log(`V is ${v.show()}`)
                var store_value =  v.value.replace(/'/g, '"');
                $('#nameNodeTree').html(k);
                $('#valueNodeTree').html(library.json.prettyPrint(JSON.parse(store_value)));

                desired_uri = k.replace("afos", "dfos");
                $('#keyForm').val(desired_uri);
                $('#valueForm').val(v.value);
            });

        }).jstree();


        astore.get(ahome+'/~stores~',function(k, stores){
            console.log(`get ${k} ->  ${stores.show()}`)
            stores.foreach(function(sids){
            sids = sids.replace(/'/g, '"');
            sids = JSON.parse(sids)
            console.log(`Stores ->  ${sids}`)
                sids.forEach(function(id){
                    console.log(`Store id ${id}`)
                    astore.get(aroot+'/'+id+'/~keys~', function(k, keys){
                        console.log(`get ${k} ->  ${keys.show()}`)
                        keys.foreach(function(list_key){
                            list_key = list_key.replace(/'/g, '"');
                            list_key = JSON.parse(list_key)
                            console.log(`Keys ${list_key}`)
                            list_key.forEach(function(key){
                                console.log(`Key ->  ${key}`)
                                add_node_actual(key);
                            });
                        });
                    });
                });

            });
        });
    })
}


function refreshdtree()
{
    $(function () {
        $('#jstree-desired').jstree(
            {
                "core" : {
                    check_callback : true,
                    "themes" : { "icons": true }
                }
            });

        $('#jstree-desired').on('changed.jstree', function (e, data) {
            var i, j, r = [];
            for(i = 0, j = data.selected.length; i < j; i++) {
                r.push(data.instance.get_node(data.selected[i]).id);
            }
            var node = $('#jstree-desired').jstree().get_node(r);
            dstore.get(node.id, function(k, v) {
                document.getElementById("main").style.display = "block";
                console.log(`Key ${k}`)
                console.log(`Value ${v.value}`)
                console.log(`V is ${v.show()}`)
                var store_value =  v.value.replace(/'/g, '"');
                $('#nameNodeTree-desired').html(k);
                $('#valueNodeTree-desired').html(library.json.prettyPrint(JSON.parse(store_value)));
                $('#keyForm').val(k);
                $('#valueForm').val(v.value);
            });

        }).jstree();


        dstore.get(dhome+'/~stores~',function(k, stores){
            console.log(`get ${k} ->  ${stores.show()}`)
            stores.foreach(function(sids){
            sids = sids.replace(/'/g, '"');
            sids = JSON.parse(sids)
            console.log(`Stores ->  ${sids}`)
                sids.forEach(function(id){
                    console.log(`Store id ${id}`)
                    dstore.get(droot+'/'+id+'/~keys~', function(k, keys){
                        console.log(`get ${k} ->  ${keys.show()}`)
                        keys.foreach(function(list_key){
                            list_key = list_key.replace(/'/g, '"');
                            list_key = JSON.parse(list_key)
                            console.log(`Keys ${list_key}`)
                            list_key.forEach(function(key){
                                console.log(`Key ->  ${key}`)
                                add_node_desired(key);
                            });
                        });
                    });
                });

            });
        });
    })
}

function refreshpage()
{
    var akeyElem = document.getElementById('nameNodeTree').innerHTML;
    if (akeyElem  != ""){
        astore.get(akeyElem, function(k, v) {

            if (v.value != null)
            {
                 var store_value =  v.value.replace(/'/g, '"');
                $('#valueNodeTree').html(library.json.prettyPrint(JSON.parse(store_value)));
                if (document.getElementById('valueNodeTree').classList.contains('node_active')) {
                    return false;
                }
                document.getElementById('valueNodeTree').classList.remove("node_disable")
                document.getElementById('valueNodeTree').classList.add("node_active")
                document.getElementById('nameNodeTree').classList.remove("node_disable")
                document.getElementById('nameNodeTree').classList.add("node_active")
            }
            else
            {
                $('#valueNodeTree').html("UNDEFINED");
                if (document.getElementById('valueNodeTree').classList.contains('node_disable')) {
                    return false;
                }
                document.getElementById('valueNodeTree').classList.remove("node_active")
                document.getElementById('valueNodeTree').classList.add("node_disable")
                document.getElementById('nameNodeTree').classList.remove("name_active")
                document.getElementById('nameNodeTree').classList.add("node_disable")

            }
        });
    }

    var dkeyElem = document.getElementById('nameNodeTree-desired').innerHTML;
    if (dkeyElem  != ""){
        dstore.get(dkeyElem, function(k, v) {

            if (v.value != null)
            {
                var store_value =  v.value.replace(/'/g, '"');
                $('#valueNodeTree-desired').html(library.json.prettyPrint(JSON.parse(store_value)));
                if (document.getElementById('valueNodeTree-desired').classList.contains('node_active')) {
                    return false;
                }
                document.getElementById('valueNodeTree-desired').classList.remove("node_disable")
                document.getElementById('valueNodeTree-desired').classList.add("node_active")
                document.getElementById('nameNodeTree-desired').classList.remove("node_disable")
                document.getElementById('nameNodeTree-desired').classList.add("node_active")
            }
            else
            {
                $('#valueNodeTree-desired').html("UNDEFINED");
                if (document.getElementById('valueNodeTree-desired').classList.contains('node_disable')) {
                    return false;
                }
                document.getElementById('valueNodeTree-desired').classList.remove("node_active")
                document.getElementById('valueNodeTree-desired').classList.add("node_disable")
                document.getElementById('nameNodeTree-desired').classList.remove("name_active")
                document.getElementById('nameNodeTree-desired').classList.add("node_disable")

            }
        });
    }
}

function add_node_actual(name)
{
    if($("#jstree").jstree("get_node", name) == false)
    {
        if (name == aroot)
        {
            return
        }

        var rootParent = aroot;
        if ($("#jstree").jstree("get_node", rootParent) == false)
        {
            $('#jstree').jstree(
                'create_node',
                '#',
                {"text": rootParent, "id": rootParent, "state": {"opened": "true", "disabled":"true"}},
                'last', false, false);
        }

        var tab = name.split(aroot + '/')[1].split('/');
        var parent = aroot
        var newNode = parent + '/' + tab[0];
        for (var i = 0; i < tab.length; i++) {
            var node1 = $("#jstree").jstree("get_node", parent);
            var node2 = $("#jstree").jstree("get_node", newNode);
            if ((node1 != false) && (node2 == false)) {
                console.log("CREATE")
                $('#jstree').jstree(
                    'create_node',
                    parent,
                    {"text": tab[i], "id": newNode, "state": {"opened": "true"}, "li_attr":{"class":"node_disable"}},
                    'last', false, false);
            }
            parent = parent + "/" + tab[i];
            if (tab[i + 1] != null) {
                newNode = newNode + '/' + tab[i + 1];
            }
        }

    }
    else
    {
        var nodeName = $("#jstree").jstree("get_node", name)
        if (document.getElementById(nodeName.id) == null)
        {
            return false;
        }

        if (document.getElementById(nodeName.id).classList.contains("node_active"))
        {
            return false;
        }
        document.getElementById(nodeName.id).classList.remove("node_disable")
        document.getElementById(nodeName.id).classList.add("node_active")
    }

}


function add_node_desired(name)
{
    if($("#jstree-desired").jstree("get_node", name) == false)
    {
        if (name == droot)
        {
            return
        }

        var rootParent = droot;
        if ($("#jstree-desired").jstree("get_node", rootParent) == false)
        {
            $('#jstree-desired').jstree(
                'create_node',
                '#',
                {"text": rootParent, "id": rootParent, "state": {"opened": "true", "disabled":"true"}},
                'last', false, false);
        }

        var tab = name.split(droot + '/')[1].split('/');
        var parent = droot
        var newNode = parent + '/' + tab[0];
        for (var i = 0; i < tab.length; i++) {
            var node1 = $("#jstree-desired").jstree("get_node", parent);
            var node2 = $("#jstree-desired").jstree("get_node", newNode);
            if ((node1 != false) && (node2 == false)) {
                console.log("CREATE")
                $('#jstree-desired').jstree(
                    'create_node',
                    parent,
                    {"text": tab[i], "id": newNode, "state": {"opened": "true"}, "li_attr":{"class":"node_disable"}},
                    'last', false, false);
            }
            parent = parent + "/" + tab[i];
            if (tab[i + 1] != null) {
                newNode = newNode + '/' + tab[i + 1];
            }
        }

    }
    else
    {
        var nodeName = $("#jstree-desired").jstree("get_node", name)
        if (document.getElementById(nodeName.id) == null)
        {
            return false;
        }

        if (document.getElementById(nodeName.id).classList.contains("node_active"))
        {
            return false;
        }
        document.getElementById(nodeName.id).classList.remove("node_disable")
        document.getElementById(nodeName.id).classList.add("node_active")
    }

}


var radio = function getRadio() {
    var radios = document.getElementsByName('check');
    for (var i = 0; i < radios.length; i++) {
        if (radios[i].checked) {
            return radios[i].value;
        }
    }
}

var select = function getSelect() {
    var selects = document.getElementById('select');
    return selects.options[selects.selectedIndex].innerHTML;
}


