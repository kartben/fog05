# This file contain the implementation of a proxy Store for interacting
# with fog05. Through this API any JS-based runtime can interact with the
# distributed store used by fog05. As such it can access the full power of
# fog05


root = this
z_ = require('./coffez.js').coffez
WebSocket = require('ws')

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
  constructor: (@oid, @sid, @rest) ->
    @cid = 'OK'
  show: () ->
    args = @rest.reduce((a, x) -> a + " " + x)
    "#{@cid} #{@oid} #{@sid} #{@args}"

class NOK
  constructor: (@oid, @sid) ->
    @cid = 'NOK'
  show: () ->
    "#{@cid} #{@oid} #{@sid}"

class Create
  constructor: (@sid, @root, @home, @cache_size) ->
    @cid = 'create'
  show: () ->
    "#{@cid} #{@sid} #{@root} #{@home} #{@cache_size}"

class Put
  constructor: (@sid, @uri, @value) ->
    @cid = 'put'
  show: () ->
    "#{@cid} #{@sid} #{@uri} #{@value}"

class Get
  constructor: (@sid, @uri) ->
    @cid = 'get'
  show: () ->
    "#{@cid} #{@sid} #{@uri}"

class GetAll
  constructor: (@sid, @uri) ->
    @cid = 'aget'
  show: () ->
    "#{@cid} #{@sid} #{@uri}"

class Observe
  constructor: (@sid, @cookie, @uri) ->
    @cid = 'observe'
  show: () ->
    "#{@cid} #{@sid} #{@uri}"

class Notify
  constructor: (@sid, @cookie, @uri, @value) ->
    @cid = 'notify'
  show: () ->
    "#{@cid} #{@sid} #{@uri} #{@value}"

class Value
  constructor: (@sid, @key, @value) ->
    @cid = 'value'
  show: () ->
    "#{@cid} #{@sid} #{@key} #{@value}"

class Values
  constructor: (@sid, @key, @values) ->
    @cid = 'values'
  show: () ->
    str = @values.reduce((a, v) -> a + ', ' + v)
    "#{@cid} #{@sid} #{@key} [#{str}]"

class GetKeys
  constructor: (@sid) ->
    @cid = 'gkeys'
  show: () ->
    "#{@cid} #{@sid}"

class Keys
  constructor: (@sid, @keys) ->
    @cid = 'keys'
  show: () ->
    str= @keys.reduce((a, v) -> a + ', ' + v)
    "#{@cid} #{@sid} [#{str}]"

Parser = {}
Parser.parseOK = (ts) ->
  if ts.length > 2
    z_.Some(new OK(ts[1], ts[2], ts[3..]))
  else
    z_.None

Parser.parseNOK = (ts) ->
  if ts.length > 2
    z_.Some(new NOK(ts[1], ts[2]))
  else
    z_.None

Parser.parseNotify = (ts) ->
  if ts.length > 4
    z_.Some(new Notify(ts[1], ts[2], ts[3], tr[4]))
  else
    z_.None

Parser.parseValue = (ts) ->
  if ts.length == 3
    z_.Some(new Value(ts[1], ts[2], z_.None))
  else if ts.length > 3
    z_.Some(new Value(ts[1], ts[2], z_.Some(ts[3])))
  else
    z_.None

Parser.parseValues = (ts) ->
  if ts.length == 3
    z_.Some(new Values(ts[1], ts[2], []))
  else if ts.length > 3
    xs = ts[3].split(',').map((x) -> x.split('@'))
    z_.Some(new Values(ts[1], ts[2], xs))
  else
    z_.None

Parser.parseKeys = (ts) ->
  if ts.length > 2
    xs = ts[2].split(',')
    z_.Some(new Keys(ts[1], xs))
  else
    z_.None


Parser.parseCmd = (cmd) ->
  tokens = (x for x in cmd.split(' ') when x != '')
  if tokens.length == 0
    z_.None
  else
    t = tokens[0]
    switch t
      when 'OK'
        Parser.parseOK(tokens)
      when 'NOK'
        Parser.parseNOK(tokens)
      when 'notify'
        Parser.parseNotify(tokens)
      when 'value'
        Parser.parseValue(tokens)
      when 'values'
        Parser.parseValues(tokens)
      when 'keys'
        Parser.parseKeys(tokens)
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
    @storeMap = {}


  generateCookie: () ->
    id = @cookieId
    @cookieId += 1
    id

  # Establish a connection with the dscript.play server
  connect: () =>
    if @connected is false
      console.log("Connecting to: #{@url}")
      @pendingWebSock = z_.Some(new WebSocket(@url))

      @pendingWebSock.map (
        (s) =>
          s.onopen = () =>
            console.log('Connected to: ' + @url)
            @webSock = @pendingWebSock
            @connected = true
            # We may need to re-establish dropped data connection, if this connection is following
            # a disconnection.
            @onconnect()
      )

      @pendingWebSock.map (
        (s) => s.onclose =
          (evt) =>
            console.log("The server at #{@url} seems to have dropped the connection.")
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
    cmd = Parser.parseCmd(msg)
    smap = @storeMap
    cmd.foreach ( (c) ->
      z_.get(smap, c.sid).foreach( (s) ->
        cid = c.cid
        s.handleCommand(c))
    )

  send: (msg) ->
    @webSock.map(
      (s) -> s.send(msg)
    )

  register: (sid, store) ->
    @storeMap[sid] = store


root.fog05.Runtime = Runtime


class Store
  constructor: (@runtime, @sid, @home, @root, @cache_size) ->
    @getTable = {}
    @obsTable = {}
    @keyFun = z_.None
    @runtime.register(@sid, this)
    cmd = new Create(@sid, @home, @root, @cache_size)
    @runtime.send(cmd.show())

  put: (key, value)  ->
    cmd = new Put(@sid, key, value)
    @runtime.send(cmd.show())

  keys: (fun) ->
    @keyFun = z_.Some(fun)
    cmd = new GetKeys(@sid)
    @runtime.send(cmd.show())

  get: (key, fun) ->
    @getTable[key] = fun
    cmd = new Get(@sid, key)
    @runtime.send(cmd.show())

  getAll: (key, fun) ->
    @getTable[key] = fun
    cmd = new GetAll(@sid, key)
    @runtime.send(cmd.show())

  observe: (key, fun) ->
    cookie = @runtime.generateCookie()
    @obsTable[cookie] = fun
    cmd = new Observe(@cid, cookie, key)
    @runtime.send(cmd.show())

  handleOK: (cmd) ->
    console.log('>>> Store Handling OK')

  handleNOK: (cmd) ->
    console.log('>>> Store Handling NOK')


  handleValue: (cmd) ->
    console.log('>>> Store Handling Value')
    z_.get(@getTable, cmd.key).foreach( (fun) -> fun(cmd.key, cmd.value))

  handleValues: (cmd) ->
    console.log('>>> Store Handling Values')
    z_.get(@getTable, cmd.key).foreach( (fun) -> fun(cmd.key, cmd.values))

  handleNotify: (cmd) ->
    console.log('>>> Store Handling Notify')
    z_.get(@obsTable, cmd.cookie).foreach( (fun) -> fun(cmd.key. cmd.value) )

  handleKeys: (cmd) ->
    @keyFun.foreach( (f) -> f(cmd.keys))

  # No so elegant, but there were issues with the map of lambdas.
  handleCommand: (cmd) ->
    switch cmd.cid
      when 'NOK'
        this.handleNOK(cmd)
      when 'OK'
        this.handleOK(cmd)
      when 'value'
        this.handleValue(cmd)
      when 'values'
        this.handleValues(cmd)
      when 'keys'
        this.handleKeys(cmd)
      when 'notify'
        this.handleNotify(cmd)




root.fog05.Store = Store