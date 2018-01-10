# This file contain the implementation of a proxy Store for interacting
# with fog05. Through this API any JS-based runtime can interact with the
# distributed store used by fog05. As such it can access the full power of
# fog05

root = this
z_ = coffez
fog05 = {}

if (typeof exports isnt 'undefined')
  if (typeof module isnt 'undefined' and module.exports)
    exports = module.exports = fog05
  exports.fog05 = fog05
else
  root.fog05 = fog05

fog05.VERSION = "0.1.0"

# Commands

class OK
  constructor: (@cid, @sid, @rest) ->
  show: () ->
    args = @rest.reduce((a, x) -> a + " " + x)
    "OK #{@cid} #{@sid} #{@args}"

class NOK
  constructor: (@cid, @sid) ->
  show: () ->
    "NOK #{@cid} #{@sid}"

class Create
  constructor: (@sid, @root, @home, @cache_size) ->
  show: () ->
    "create #{@sid} #{@root} #{@home} #{@cache_size}"

class Put
  constructor: (@sid, @uri, @value) ->
  show: () ->
    "put #{@sid} #{@uri} #{@value}"

class Get
  constructor: (@sid, @uri) ->
  show: () ->
    "get #{@sid} #{@uri}"

class Observe
  constructor: (@sid, @cookie, @uri) ->
  show: () ->
    "observe #{@sid} #{@uri}"

class Notify
  constructor: (@sid, @cookie, @uri, @value) ->
  show: () ->
    "notify #{@sid} #{@uri} #{@value}"

class Value
  constructor: (@sid, @key, @value) ->
  show: () ->
    "value #{@sid} #{@key} #{@value}"

parseOK: (ts) ->
  if ts.length > 2
    z_.Some(new OK(ts[1], ts[2], ts[3..]))
  else
    z_.None

parseNOK: (ts) ->
  if ts.length > 2
    z_.Some(new NOK(ts[1], ts[2]))
  else
    z_.None

parseNotify: (ts) ->
  if ts.length > 4
    z_.Some(new Notify(ts[1], ts[2], ts[3], tr[4]))
  else
    z_.None

parseValue: (ts) ->
  if ts.length == 3
    new Value(ts[1], ts[2], z_.None)
  else if ts.length > 3
    z_.Some(new Value(ts[1], ts[2], z_.Some(ts[3])))
  else
    z_.None


parse: (cmd) ->
  tokens = (x for x in cmd.split(' ') x != '')
  if tokens.length == 0
    z_.None
  else
    t = tokens[0]
    if t == 'OK'
      parseOK(tokens)
    else if t == 'NOK'
      parseNOK(tokens)
    else if t == 'notify'
      parseNotify(tokens)
    else if t == 'value'
      parseValue(tokens)

    else
      z_.None      

# The `Runtime` maintains the connection with the server, re-establish the connection if dropped and mediates
# the `DataReader` and `DataWriter` communication.
class Runtime
  # Creates a new fog05 runtime
  constructor: (@url) ->
    @onclose = (evt) ->
    @onconnect = () ->
    @ondisconnect = (evt) ->
    @connected = false
    @closed = true
    @cookieId = 0
    @pendingWebSock = z_.None
    @webSock = z_.None
    @storeHandlersMap = {}


  generateEntityId: () ->
    id = @cookieId
    @cookieId += 1
    id

  # Establish a connection with the dscript.play server
  connect: () =>
    if @connected is false
      console.log("Connecting to: #{url}")
      @pendingWebSock = new z_.Some(new WebSocket(url))

      @pendingWebSock.map (
        (s) =>
          s.onopen = () =>
            console.log('Connected to: ' + @uri)
            @webSock = @pendingWebSock
            @connected = true
            # We may need to re-establish dropped data connection, if this connection is following
            # a disconnection.
            @onconnect()
      )

      @pendingWebSock.map (
        (s) => s.onclose =
          (evt) =>
            console.log("The server at #{@uri} seems to have dropped the connection.")
            @connected = false
            @webSock.close()
            @closed = true
            @webSock = z_.None
            @ondisconnect(evt)
      )


      @pendingWebSock.map (
        (s) =>
          s.onmessage = (msg) =>
            this.handleMessage(msg)
      )
    else
      console.log("Warning: Trying to connect an already connected Runtime")


  # Disconnects, withouth closing, a `Runtime`. Notice that there is a big difference between disconnecting and
  # closing a `Runtime`. The a disconnected `Runtime` can be reconnected and retains state across
  # connection/disconnections. On the other hand, once closed a `Runtime` clears up all current state.
  disconnect: () =>
    @connected = false
    @webSock.map(
      (s) -> s.close()
    )
    @ondisconnect()


  # Close the fog05 runtime and as a consequence all the `DataReaders` and `DataWriters` that belong to this runtime.
  close: () =>
    @webSock.map (
      (s) =>
        s.close()
        this.onclose()
    )

  isConnected: () => @connected

  isClosed: () => @closed


  handleMessage: (s) =>
    msg = s.data
    console.log('received'+ msg)
    cmd = parse(msg)
    handlers = @storeHandlersMap
    cmd.map ( (c) ->
      h = handlers[c.cid]
      if h? == true
        h(c)
    )



  send: (msg) ->
    @webSock.map(
      (s) -> s.send(msg)
    )

  register: (sid, handlers) ->
    @storeHandlersMap[sid] = handlers


root.fog05.Runtime = Runtime

class Store
  constructor: (@runtime, @sid, @home, @root, @cache_size) ->
    @getTable = {}
    @obsTable = {}
    @handlers = {
      OK: (cmd) -> self.handleOK(cmd),
      NOK: (cmd) -> self.handleNOK(cmd)
      notify: (cmd) -> self.handleNotify(cmd)
      value: (cmd) -> self.handleValue(cmd)
    }
    runtime.register(@sid, @handlers)
    cmd = new Create(@sid, @home, @root, @cache_size)
    @runtime.send(cmd.show())

  put: (key, value)  ->
    cmd = new Put(@sid, @key, @value)
    @runtime.send(cmd.show())

  get: (fun) -> (key) ->
    @getTable[key] = fun
    cmd = new Get(@sid, key)
    @runtime.send(cmd.show())

  observe: (key, cookie, fun) ->
    @obsTable[cookie] = fun
    cmd = new Observe(@cid, @cookie, @uri)
    @runtime.send(cmd.show())

  handleOK: (cmd) ->
    console.log('Store Handling OK')

  handleValue: (cmd) ->
      fun = @getTable[cmd.key]
      if fun? == true
        fun(cmd.key, cmd.value)

  handleNotify: (cmd) ->
    console.log('Store Handling Notify')
    fun = @obsTable[cmd.cookie]
    if fun? == true
      fun(cmd.key. cmd.value)

  handleNOK: (cmd) ->
    console.log('Store Handling NOK')

