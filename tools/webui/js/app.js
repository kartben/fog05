var store;
var storeid;
var store_root;
var store_home;

var wsconnect = function wsconnect() {

    var rootString = document.getElementById('root').value;
    if (rootString == "")
    {
        alert('Please enter a value for "Root"');
    }
    else
    {
        display();
        var rootString = document.getElementById('root').value;

        store_root = rootString;
        store_home = rootString+'/web';

        document.getElementById('keyForm').value = rootString;
        var fos = this.fog05;
        var rt = new fos.Runtime(document.getElementById('connect').value);
        var storeid = document.getElementById('storeid').value;
        rt.onconnect = function () {

            store = new fos.Store(rt, storeid, store_root, store_home, 1024);
            refresh()
        };
        rt.connect();
        setInterval(function(){refresh();}, 10000);
    }
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
    refreshtree()
    refreshpage()
}

function refreshtree()
{
    $(function () {
        $('#jstree').jstree(
            {
                "core" : {
                    check_callback : true,
                    "themes" : { "icons": false }
                }
            });

        $('#jstree').on('changed.jstree', function (e, data) {
            var i, j, r = [];
            for(i = 0, j = data.selected.length; i < j; i++) {
                r.push(data.instance.get_node(data.selected[i]).id);
            }
            var node = $('#jstree').jstree().get_node(r);
            store.get(node.id, function(k, v) {
                document.getElementById("main").style.display = "block";
                console.log(`Key ${k}`)
                console.log(`Value ${v.value}`)
                console.log(`V is ${v.show()}`)
                $('#nameNodeTree').html(k);
                $('#valueNodeTree').html(v.value);
                $('#keyForm').val(k);
                $('#valueForm').val(v.value);
            });

        }).jstree();

        // TODO see why the forEach not work
        // AC: this is a mis-spelling as for the None monad the method
        //     is called foreach.
        store.get(store_home+'/~stores~',function(k, stores){
            console.log(`get ${k} ->  ${stores.show()}`)
            stores.foreach(function(sid){
                sid = sid.slice(2,-2);
                console.log(`Store id ${sid}`)
                store.get(store_root+'/'+sid+'/~keys~', function(k, keys){
                    console.log(`get ${k} ->  ${keys.show()}`)
                    keys.foreach(function(key){
                        console.log(`Key ${key}`)
                        add_node(key);
                    });
                });
            });
        });

//        store.keys(function (keys){
//            keys.forEach(function(key){
//                add_node(key);
//            });
//        });
    })
}

function refreshpage()
{
    var keyElem = document.getElementById('nameNodeTree').innerHTML;
    if (keyElem  != ""){
        store.get(keyElem, function(k, v) {

            if (v.value != null)
            {
                $('#valueNodeTree').html(v.value);
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
}

function add_node(name)
{
    if($("#jstree").jstree("get_node", name) == false)
    {
        if (name == document.getElementById('root').value)
        {
            return
        }

        var rootParent = document.getElementById('root').value;
        if ($("#jstree").jstree("get_node", rootParent) == false)
        {
            $('#jstree').jstree(
                'create_node',
                '#',
                {"text": rootParent, "id": rootParent, "state": {"opened": "true", "disabled":"true"}},
                'last', false, false);
        }

        var tab = name.split((document.getElementById('root').value) + '/')[1].split('/');
        var parent = document.getElementById('root').value;
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



