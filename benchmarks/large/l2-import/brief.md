# How does Python's import statement find and load a module?

Reader: a developer new to the topic
Medium: screen

Source: CPython 3.13 `importlib/_bootstrap.py` and `importlib/_bootstrap_external.py`. Node names follow the real function names. Kinds: start, end, fail, step, decision, item (a member of a set). A set is a titled list of members that apply together; each set says whether it is ordered. `S1 -> x` means the flow leaves the whole set. `x -> S1` means the flow enters the whole set.

## Stage A: Entry through __import__

Nodes
- a01 | import statement | start
- a02 | __import__ | step
- a03 | Level is zero? | decision
- a04 | _calc___package__ | step
- a09 | Fromlist empty? | decision
- a10 | Absolute import? | decision
- a11 | Return top-level package | end
- a12 | Return leading name part | end
- a13 | Module has __path__? | decision
- a14 | Return module | end
- a15 | _handle_fromlist | step
- a19 | Attribute exists? | decision
- a20 | Import submodule | step
- a23 | Return module with names | end

Set S1: Package lookup order (ordered, each is tried only if the one before gave nothing)
- a05 | Read __package__ | item
- a06 | Read __spec__.parent | item
- a07 | Read __name__ | item

Connections
- a01 -> a02
- a02 -> a03
- a03 -> b01 : yes
- a03 -> a04 : no
- a04 -> S1
- S1 -> b01
- b13 -> a09
- a09 -> a10 : yes
- a09 -> a13 : no
- a10 -> a11 : yes
- a10 -> a12 : no
- a13 -> a14 : no
- a13 -> a15 : yes
- a15 -> a19
- a19 -> a23 : yes
- a19 -> a20 : no
- a20 -> b01 : parent.name
- a20 -> a23

## Stage B: _gcd_import and argument checks

Nodes
- b01 | _gcd_import | step
- b02 | _sanity_check | step
- b03 | Arguments valid? | decision
- b04 | Argument error raised | fail
- b07 | Level above zero? | decision
- b11 | _resolve_name | step
- b12 | Enough package parts? | decision
- b14 | ImportError beyond top-level | fail
- b15 | _find_and_load | step
- b13 | Module returned | step

Connections
- b01 -> b02
- b02 -> b03
- b03 -> b04 : no
- b03 -> b07 : yes
- b07 -> b11 : yes
- b07 -> b15 : no
- b11 -> b12
- b12 -> b14 : no
- b12 -> b15 : yes
- b15 -> c01

## Stage C: The sys.modules cache and module locks

Nodes
- c01 | Look up sys.modules | step
- c02 | Cached module found? | decision
- c03 | Still initializing? | decision
- c05 | Cached value is None? | decision
- c06 | ModuleNotFoundError None cached | fail
- c07 | _ModuleLockManager enter | step
- c10 | Deadlock detected? | decision
- c11 | _DeadlockError | fail
- c12 | Look up again | step
- c13 | Still missing? | decision

Connections
- c01 -> c02
- c02 -> c07 : no
- c02 -> c03 : yes
- c03 -> c07 : yes
- c03 -> c05 : no
- c05 -> c06 : yes
- c05 -> b13 : no
- c07 -> c10
- c10 -> c11 : yes
- c10 -> c12 : no
- c12 -> c13
- c13 -> d01 : yes
- c13 -> c05 : no

## Stage D: _find_and_load_unlocked and the parent package

Nodes
- d01 | _find_and_load_unlocked | step
- d02 | Name has parent? | decision
- d03 | Parent in sys.modules? | decision
- d04 | Import parent first | step
- d07 | Parent has __path__? | decision
- d08 | ModuleNotFoundError not a package | fail
- d12 | _find_spec | step
- d13 | Spec found? | decision
- d14 | ModuleNotFoundError no module named | fail
- d16 | _load_unlocked | step
- d18 | Has parent? | decision
- d19 | setattr child on parent | step
- d22 | Return module | end

Connections
- d01 -> d02
- d02 -> d03 : yes
- d02 -> d12 : no
- d03 -> d07 : yes
- d03 -> d04 : no
- d04 -> b01 : parent name
- d04 -> d07
- d07 -> d08 : no
- d07 -> d12 : yes
- d12 -> e01
- e12 -> d13 : no
- e16 -> d13
- f19 -> d13
- f27 -> d13
- d13 -> d14 : no
- d13 -> d16 : yes
- d16 -> h01
- h21 -> d18
- d18 -> d19 : yes
- d18 -> d22 : no
- d19 -> d22
- d22 -> b13

## Stage E: _find_spec over sys.meta_path

Nodes
- e01 | _find_spec | step
- e02 | sys.meta_path is None? | decision
- e03 | ImportError meta_path None | fail
- e07 | Next finder | step
- e10 | Call finder.find_spec | step
- e11 | Spec returned? | decision
- e12 | More finders? | decision
- e14 | Reuse spec if imported | step
- e16 | Return spec | step
- e23 | _imp.is_builtin? | decision
- e24 | Spec from loader built-in | step
- e25 | _imp.find_frozen | step
- e26 | Frozen info found? | decision
- e27 | Spec from loader frozen | step

Set S2: Default sys.meta_path (ordered, tried in this order)
- e20 | BuiltinImporter | item
- e21 | FrozenImporter | item
- e22 | PathFinder | item

Connections
- e01 -> e02
- e02 -> e03 : yes
- e02 -> S2 : no
- S2 -> e07
- e07 -> e10
- e10 -> e11
- e11 -> e14 : yes
- e11 -> e12 : no
- e12 -> e07 : yes
- e14 -> e16
- e20 -> e23
- e23 -> e24 : yes
- e23 -> e11 : no
- e24 -> e11
- e21 -> e25
- e25 -> e26
- e26 -> e27 : yes
- e26 -> e11 : no
- e27 -> e11
- e22 -> f01

## Stage F: PathFinder, sys.path, path_hooks and path_importer_cache

Nodes
- f01 | PathFinder.find_spec | step
- f05 | Next path entry | step
- f07 | _path_importer_cache | step
- f10 | Entry in importer cache? | decision
- f11 | _path_hooks | step
- f13 | Hook accepts entry? | decision
- f14 | More hooks? | decision
- f15 | Cache finder or None | step
- f16 | Finder is None? | decision
- f17 | finder.find_spec | step
- f18 | Spec returned? | decision
- f19 | Return spec | step
- f20 | Spec has loader? | decision
- f21 | ImportError spec missing loader | fail
- f22 | Remember namespace portions | step
- f23 | Entries exhausted? | decision
- f24 | Wrap in _NamespacePath | step
- f25 | Any portions? | decision
- f27 | Return None | step
- f28 | Spec has portions? | decision

Set S3: Default sys.path_hooks (ordered, tried in this order)
- f30 | zipimporter | item
- f31 | FileFinder.path_hook | item

Connections
- f01 -> f05 : path defaults to sys.path
- f05 -> f07
- f07 -> f10
- f10 -> f16 : yes
- f10 -> f11 : no
- f11 -> S3
- S3 -> f13
- f13 -> f15 : yes
- f13 -> f14 : no
- f14 -> S3 : yes
- f14 -> f15 : no
- f15 -> f16
- f16 -> f23 : yes
- f16 -> f17 : no
- f17 -> g01
- g20 -> f18
- g16 -> f18
- g17 -> f18
- f18 -> f23 : no
- f18 -> f20 : yes
- f20 -> f19 : yes
- f20 -> f28 : no
- f28 -> f21 : no
- f28 -> f22 : yes
- f22 -> f23
- f23 -> f05 : no
- f23 -> f25 : yes
- f25 -> f24 : yes
- f25 -> f27 : no
- f24 -> f19

## Stage G: FileFinder and its loaders

Nodes
- g01 | FileFinder.find_spec | step
- g04 | _fill_cache | step
- g05 | Name is a directory? | decision
- g07 | __init__ file found? | decision
- g12 | File with suffix found? | decision
- g15 | Directory seen earlier? | decision
- g16 | Return spec without loader | step
- g17 | Return None | step
- g18 | spec_from_file_location | step
- g19 | Create loader instance | step
- g20 | Set origin and cached | step

Set S4: Loader order in FileFinder (ordered, the first matching suffix wins)
- g30 | Extension loader (.so) | item
- g31 | Source loader (.py) | item
- g32 | Bytecode loader (.pyc) | item

Set S5: Extension module suffixes (ordered, from _imp.extension_suffixes)
- g33 | .cpython-313-x86_64-linux-gnu.so | item
- g34 | .abi3.so | item
- g35 | .so | item

Connections
- g01 -> g04 : refresh if directory changed
- g04 -> g05
- g05 -> S4 : yes
- g05 -> S5 : no
- S4 -> g07
- g07 -> g18 : yes
- g07 -> S5 : no
- S5 -> g12
- g12 -> g18 : yes
- g12 -> g15 : no
- g15 -> g16 : yes
- g15 -> g17 : no
- g18 -> g19
- g19 -> g20

## Stage H: module_from_spec and _load_unlocked

Nodes
- h01 | _load_unlocked | step
- h07 | module_from_spec | step
- h09 | loader.create_module | step
- h10 | Result is None? | decision
- h11 | _new_module | step
- h12 | _init_module_attrs | step
- h14 | Put module in sys.modules | step
- h15 | Loader is None? | decision
- h17 | ImportError missing loader | fail
- h24 | loader.exec_module | step
- h18 | Execution raised? | decision
- h20 | Remove module and re-raise | fail
- h21 | Reinsert from sys.modules | step

Set S6: Module attributes set (unordered, all set by _init_module_attrs)
- h30 | __name__ | item
- h31 | __loader__ | item
- h32 | __package__ | item
- h33 | __spec__ | item
- h34 | __path__ | item
- h35 | __file__ | item
- h36 | __cached__ | item

Connections
- h01 -> h07
- h07 -> h09
- h09 -> h10
- h10 -> h11 : yes
- h10 -> h12 : no
- h11 -> h12
- h12 -> S6
- S6 -> h14
- h14 -> h15
- h15 -> h17 : yes
- h15 -> h24 : no
- h24 -> i00
- i05 -> h18
- i12 -> h18
- i20 -> h18
- i22 -> h18
- h18 -> h20 : yes
- h18 -> h21 : no

## Stage I: Loader dispatch and execution

Nodes
- i00 | Which loader? | decision
- i01 | _LoaderBasics.exec_module | step
- i02 | SourceLoader.get_code | step
- i05 | exec code in __dict__ | step
- i12 | _imp.exec_dynamic | step
- i13 | SourcelessFileLoader.get_code | step
- i15 | _classify_pyc | step
- i16 | _compile_bytecode | step
- i17 | ImportError bad magic number | fail
- i20 | _imp.exec_builtin | step
- i22 | Exec frozen code | step

Connections
- i00 -> i01 : source file
- i00 -> i13 : bytecode only
- i00 -> i12 : extension
- i00 -> i20 : built-in
- i00 -> i22 : frozen
- i01 -> i02
- i02 -> j02
- j31 -> i05
- i13 -> i15
- i15 -> i17 : bad magic
- i15 -> i16 : valid header
- i16 -> i05

## Stage J: Source get_code and the bytecode cache checks

Nodes
- j02 | cache_from_source | step
- j03 | Stat and pyc readable? | decision
- j09 | _classify_pyc | step
- j10 | Magic number matches? | decision
- j11 | Bad magic ImportError | step
- j12 | Ignore cached bytecode | step
- j15 | Header and flags valid? | decision
- j17 | Hash-based pyc? | decision
- j19 | Mtime and size match? | decision
- j22 | Source check wanted? | decision
- j27 | Source hash matches? | decision
- j29 | Accept cached bytecode | step
- j30 | _compile_bytecode | step
- j31 | Return code object | end
- j32 | source_to_code | step
- j33 | Bytecode may be written? | decision
- j34 | Hash-based layout? | decision
- j35 | _code_to_hash_pyc | step
- j36 | _code_to_timestamp_pyc | step
- j37 | _cache_bytecode | step

Connections
- j02 -> j03
- j03 -> j32 : no
- j03 -> j09 : yes
- j09 -> j10
- j10 -> j11 : no
- j10 -> j15 : yes
- j11 -> j12
- j15 -> j12 : no
- j15 -> j17 : yes
- j17 -> j19 : no
- j17 -> j22 : yes
- j19 -> j29 : yes
- j19 -> j12 : no
- j22 -> j27 : flag set or always
- j22 -> j29 : flag clear or never
- j27 -> j29 : yes
- j27 -> j12 : no
- j29 -> j30
- j30 -> j31
- j12 -> j32 : read and compile source
- j32 -> j33
- j33 -> j31 : no
- j33 -> j34 : yes
- j34 -> j35 : yes
- j34 -> j36 : no
- j35 -> j37
- j36 -> j37
- j37 -> j31

Node count: 157 (136 stage nodes and 21 set members; set titles S1 to S6 are not counted)
