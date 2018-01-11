#
#                          OpenSplice Web
#
#    This software and documentation are Copyright 2010 to 2014 PrismTech
#    Limited and its licensees. All rights reserved. See file:
#
#                           docs/LICENSE_LGPL.html
#
#    for full copyright notice and license terms.
#

#
# coffez is a library that provides a few useful funcitonal abstractions such as Option and Try types
#

root = this

root.coffez = {}

# `Option` monad implementation.
None = {}
None.map = (f) -> None
None.flatMap = (f) -> None
None.get = () -> undefined
None.getOrElse = (f) -> f()
None.orElse = (f) -> f()
None.isEmpty = () -> true
None.show = () -> 'None'

class CSome
  constructor: (@value) ->
  map: (f)  -> new CSome(f(@value))
  flatMap: (f) -> f(@value)
  get: () -> @value
  getOrElse: (f) -> @value
  orElse: (f) -> this
  isEmpty: () -> false
  show: () -> 'Some('+JSON.stringify(@value)+')'


class CFail
  constructor: (@what) ->
  map: (f)  -> throw @what
  flatMap: (f) -> throw @what
  get: () -> throw @what
  getOrElse: (f) -> throw @what
  orElse: (f) -> throw @what
  isEmpty: () -> throw @what

# `Try` monad implementation.
class CSuccess
  constructor: (@value) ->
  map: (f) -> f(@value)
  get: () -> @value
  getOrElse: (f) -> @value
  orElse: (f) -> this
  isFailure: () -> false
  isSuccess: () -> true
  toOption: () -> new CSome(@value)
  recover: (f) -> this

class CFailure
  constructor: (@exception) ->
  map: (f) -> None
  get: () -> @exception
  getOrElse: (f) -> f()
  orElse: (f) -> f()
  isFailure: () -> true
  isSuccess: () -> false
  toOption: () -> None
  recover: (f) -> f(@exception)



ematch = (x, y) ->
  if (y == undefined) then true else x == y

omatch = (a, b) ->
  m = true
  for k,v of a
    e = match(v, b[k])
    m = m and e
  m

match = (a, b) ->
  switch typeof(a)
    when 'object'
      switch typeof(b)
        when 'object'
          omatch(a, b)
          #if (Object.keys(a).length == Object.keys(b).length) then omatch(a, b) else false
        else
          false
    when 'function'
      false
    when 'undefined' then false
    else
      switch typeof(b)
        when 'object' then false
        when 'function' then false
        when 'undefined' then true
        else ematch(a, b)


root.coffez.None = None
root.coffez.Some = (value) -> new CSome(value)
root.coffez.Fail = (what) -> new CFail(what)
root.coffez.Success = (value) -> new CSuccess(value)
root.coffez.Failure = (ex) -> new CFailure(ex)
root.coffez.match = match
