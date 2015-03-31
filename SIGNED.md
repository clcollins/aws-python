##### Signed by https://keybase.io/clcollins
```
-----BEGIN PGP SIGNATURE-----
Version: GnuPG v1

iEYEABECAAYFAlUbAeYACgkQte6EFif3vze9BwCgyceOyUe/oD+CLSK1PewPhxGr
06UAoKFC3nakKRKMexFP9ckuUhjQ33mb
=/9HT
-----END PGP SIGNATURE-----

```

<!-- END SIGNATURES -->

### Begin signed statement 

#### Expect

```
size   exec  file                 contents                                                        
             ./                                                                                   
14             .gitignore         5a1c48902aa4e38786229ed6c871d85273e6680846fbf4a65ae5710981145d9f
35122          LICENSE            12ac5047f2af0522f06798b1589ffc4599bc29c91f954d7874e0320634e777c0
55             README.md          36d73bc04c3ea1864f8e244aa6ad0aa07ff62b3b2162b9c0ac9145ed252980c5
349            list_images.py     f8908463ff42a031199ee4c16f6125b43d4005fc6c049c82b6a1fdeb683d6eb8
423            list_instances.py  4df8fc57987c504f6e6facf14f6906fbe88442a4ccdcf94776b52d33f6bcdf50
```

#### Ignore

```
/SIGNED.md
```

#### Presets

```
git      # ignore .git and anything as described by .gitignore files
dropbox  # ignore .dropbox-cache and other Dropbox-related files    
kb       # ignore anything as described by .kbignore files          
```

<!-- summarize version = 0.0.9 -->

### End signed statement

<hr>

#### Notes

With keybase you can sign any directory's contents, whether it's a git repo,
source code distribution, or a personal documents folder. It aims to replace the drudgery of:

  1. comparing a zipped file to a detached statement
  2. downloading a public key
  3. confirming it is in fact the author's by reviewing public statements they've made, using it

All in one simple command:

```bash
keybase dir verify
```

There are lots of options, including assertions for automating your checks.

For more info, check out https://keybase.io/docs/command_line/code_signing