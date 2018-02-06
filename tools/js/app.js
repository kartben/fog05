var store
var rootString

var wsconnect = function wsconnect() {

    rootString = document.getElementById('root').value;
    if (rootString == "")
    {
        alert('Please enter a value for "Root"');
    }
    else
    {
        display();
        var rootString = document.getElementById('root').value;
      
        document.getElementById('keyForm').value = rootString;
        var fos = this.fog05;
        var rt = new fos.Runtime(document.getElementById('connect').value);
        var storeid = document.getElementById('storeid').value;
        rt.onconnect = function () {

            store = new fos.Store(rt, storeid, rootString, rootString, 1024);
            
            refresh()
        };

        rt.connect();
        
        setInterval(function(){refresh();}, 1000);
    }
}

function pushKeyValue()
{
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
		store.put(keyElem, valueElem);
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
         r.push(data.instance.get_node(data.selected[i]).text);
       }
       var node = $('#jstree').jstree().get_node(r);
       store.get(node.text, function(k, v) {
         document.getElementById("main").style.display = "block";
         $('#nameNodeTree').html(k);
         $('#valueNodeTree').html(v.value);
         $('#keyForm').val(k);
         $('#valueForm').val(v.value);
       });
  
     }).jstree();
      
     store.keys(function (keys){
        keys.forEach(function(key){
          add_node(key);
        });
     });
   })
}

function refreshpage()
{
   var keyElem = document.getElementById('nameNodeTree').innerHTML;
   if (keyElem  != ""){
      store.get(keyElem, function(k, v) {
          $('#valueNodeTree').html(v.value);
       });
    }
}

function add_node(name)
{
   if($("#jstree").jstree("get_node",name) == false)
   {
      var subname = name.substring(0, name.lastIndexOf('/'))
      while(subname.includes("//"))
      {
         var node = $("#jstree").jstree("get_node",subname)
         if(node != false)
         {
            console.log("create")
            $('#jstree').jstree(
               'create_node',
               subname,
               { "text":name, "id":name, "state":{"opened": "true"}},
               'last', false, false)
            move_brothers(name)

            return
         }
         subname = name.substring(0, subname.lastIndexOf('/'))
      }

      $('#jstree').jstree(
         'create_node',
         '#',
         { "text":name, "id":name,  "state":{"opened": "true"}},
         'last', false, false);

      move_brothers(name)
   }
}

function move_brothers(name)
{
    var children =
        $('#jstree').jstree(
            'get_json',
            $("#jstree").jstree("get_parent",name)).children

    if(children === undefined)
    {
        children =
            $('#jstree').jstree(
                'get_json',
                "#")
    }
    if(children !== undefined) {
        children.forEach(function (bro) {
            if (bro.id.startsWith(name)) {
                $('#jstree').jstree().move_node(bro.id, name, "last", false, false, false);
            }
        })
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




