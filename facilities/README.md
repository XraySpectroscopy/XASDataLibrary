# Facilities and beamline metadata #

## Facilities

The file `lightsources.org.json` was kindly provided by Danielle from
lighsources.org and Jim Birch of
[Xeno Media](http://www.xenomedia.com/).  In contains the data the
goes into the big table at
[the Light Sources of the World page](http://www.lightsources.org/regions)
as well as the contain information for each facilitiy.

Unfortunately, the contact information in that file is very messy --
inconsistent content, inconsistent formatting -- so the quick-n-dirty
perl script `munge_json.pl` was written to sanitize the content and
rewrite it into JSON file with entries that look like this:

```json
  "PETRA III": {
    "phone": "+49 40 / 8998-1541",
    "website": "http://photon-science.desy.de",
    "email": "photon-science@desy.de",
    "fullname": "PETRA III at DESY",
    "country": "Germany",
    "post": "DESY Photon Science\nNotkestr. 85\n22607 HAMBURG\nGermany",
    "fax": "+49 40 / 8998-4475"
  }
```

Two files were produced, `synchrotrons.json` contains metadata about
the world's 47 synchrotrons and `fels.json` with metadata about the
world's 13 free-electron lasers.

There is data about other facilties in the file provided by
lightsources.org and Xeno Media.  For example, data about United
States Department of Energy nanomaterials user facilities is in the
file.  As those are not places where XAS is measured
(well... OK... one can measure EELS on an electron microscope... but
the [XDI](https://github.com/XraySpectroscopy/XAS-Data-Interchange)
dictionary does not yet have definitions suitable for EELS
mesaurements)those items have not been sanitized.


## Beamlines

