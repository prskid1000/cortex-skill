# Web Parsing Reference (lxml + BeautifulSoup4)

---

## lxml

### Installation
```
pip install lxml
import lxml.etree as etree
import lxml.html
```

---

### ElementTree API

#### Parse
```python
tree = etree.parse("file.xml")                       # from file
tree = etree.parse(StringIO(xml_string))              # from string IO
root = etree.fromstring(xml_bytes)                    # from bytes -> Element
root = etree.XML("<root><child/></root>")             # from string literal
doc  = etree.ElementTree(root)                        # wrap Element in tree
```

#### Create elements
```python
root = etree.Element("root", attrib={"id": "1"})     # create element
child = etree.SubElement(root, "child")               # append sub-element
child.text = "content"                                # set text
child.tail = "text after closing tag"                 # set tail text
child.set("attr", "value")                            # set attribute
child.get("attr")                                     # get attribute
del child.attrib["attr"]                              # delete attribute
```

#### E-factory (declarative construction)
```python
from lxml.builder import E
html = E.html(
    E.head(E.title("Page")),
    E.body(E.p("Paragraph", {"class": "intro"}))
)
```

#### Modify
```python
root.append(element)           # append child
root.insert(0, element)        # insert at index
root.remove(element)           # remove child
root.replace(old, new)         # replace child
root.addnext(sibling)          # add following sibling
root.addprevious(sibling)      # add preceding sibling
root.getparent()               # parent element
root.getprevious()             # previous sibling
root.getnext()                 # next sibling
list(root)                     # list children
len(root)                      # count children
root.index(child)              # index of child
```

#### Iterate
```python
for child in root:                        # direct children
for elem in root.iter():                  # all descendants
for elem in root.iter("tag"):            # descendants with tag
for elem in root.iter("tag1", "tag2"):   # multiple tags
root.iterchildren()                       # children iterator
root.itersiblings()                       # following siblings
root.iterancestors()                      # ancestor chain
root.iterdescendants()                    # all descendants
root.itertext()                           # all text content
```

#### Serialize
```python
etree.tostring(root, pretty_print=True, encoding="unicode")
etree.tostring(root, method="html", encoding="utf-8")    # bytes
etree.tostring(root, xml_declaration=True, encoding="UTF-8")
etree.indent(root, space="  ")                            # in-place indent
tree.write("output.xml", pretty_print=True, xml_declaration=True, encoding="UTF-8")
etree.tostring(root, method="c14n")                       # C14N canonical
etree.tostring(root, method="c14n2")                      # C14N 2.0
```

---

### XPath 1.0

#### Basic queries
```python
root.xpath("//div")                               # all div elements
root.xpath("//div[@class='main']")                # attribute filter
root.xpath("//div/p/text()")                      # text content
root.xpath("//a/@href")                           # attribute values
root.xpath("count(//p)")                          # count (returns float)
root.xpath("//p[position()>2]")                   # positional
root.xpath("//p[last()]")                         # last element
root.xpath("//div[contains(@class,'item')]")      # contains
root.xpath("//div[starts-with(@id,'sec')]")       # starts-with
root.xpath("//h1 | //h2 | //h3")                 # union
root.xpath("//div[not(@hidden)]")                 # negation
root.xpath("normalize-space(//title)")            # normalize whitespace
root.xpath("string(//title)")                     # string value
```

#### XPath axes
`self`, `child`, `parent`, `ancestor`, `ancestor-or-self`, `descendant`, `descendant-or-self`, `following`, `following-sibling`, `preceding`, `preceding-sibling`, `attribute`, `namespace`

#### Compiled XPath
```python
find = etree.XPath("//div[@class=$cls]")
results = find(root, cls="main")                  # parameterized

evaluator = etree.XPathEvaluator(root)
results = evaluator("//p")

find = etree.ETXPath("//{http://ns.example.com}tag")  # namespace-aware
results = find(root)
```

#### EXSLT extensions
Supported namespaces: `regexp`, `set`, `math`, `string`, `date`
```python
ns = {"re": "http://exslt.org/regular-expressions"}
root.xpath("//a[re:test(@href, 'https?://')]", namespaces=ns)
```

---

### XSLT Transformations

```python
xslt_tree = etree.parse("transform.xsl")
transform = etree.XSLT(xslt_tree)
result = transform(doc)                            # apply
result = transform(doc, param1="'value'")          # string parameter
result = transform(doc, param1=etree.XSLT.strparam("value"))
print(str(result))                                 # serialized output
print(transform.error_log)                         # error log

# Profiling
result = transform(doc, profile_run=True)
print(result.xslt_profile.text)

# Access control
ac = etree.XSLTAccessControl(read_file=True, write_file=False,
                              create_dir=False, read_network=False,
                              write_network=False)
transform = etree.XSLT(xslt_tree, access_control=ac)
```

---

### Validation

#### XML Schema (XSD)
```python
schema_doc = etree.parse("schema.xsd")
schema = etree.XMLSchema(schema_doc)
schema.validate(doc)                       # returns bool
schema.assertValid(doc)                    # raises on invalid
schema.error_log                           # validation errors
parser = etree.XMLParser(schema=schema)    # validate during parse
```

#### RelaxNG
```python
rng_doc = etree.parse("schema.rng")
rng = etree.RelaxNG(rng_doc)
rng.validate(doc)
rng.error_log

# Compact syntax
rng = etree.RelaxNG.from_rnc_string("element root { text }")
```

#### Schematron
```python
schematron_doc = etree.parse("rules.sch")
schematron = etree.Schematron(schematron_doc)
schematron.validate(doc)
report = schematron.validation_report       # SVRL XML report
```

#### DTD
```python
dtd = etree.DTD("schema.dtd")
dtd = etree.DTD(StringIO("<!ELEMENT root (child+)>"))
dtd.validate(doc)
dtd.error_log
```

---

### lxml.html

#### Parse
```python
import lxml.html
doc = lxml.html.fromstring(html_string)
doc = lxml.html.parse("http://example.com")        # URL or file
doc = lxml.html.document_fromstring(html_string)    # full document
doc = lxml.html.fragment_fromstring(html_string)    # fragment
elements = lxml.html.fragments_fromstring(html_str) # multiple fragments
```

#### Element methods
```python
elem.text_content()        # all text (recursive)
elem.drop_tree()           # remove element and children
elem.drop_tag()            # remove tag, keep children/text
elem.classes                # set of CSS classes
elem.base_url              # resolved base URL
```

#### Links
```python
doc.make_links_absolute("http://base.url/")
doc.resolve_base_href()
for element, attribute, link, pos in doc.iterlinks():
    pass                    # iterate all links
doc.rewrite_links(lambda href: href.replace("old", "new"))
```

#### Forms
```python
for form in doc.forms:
    print(form.action, form.method)
    print(form.fields)               # dict-like
    form.fields["input_name"] = "value"
```

#### Cleaner
```python
from lxml.html.clean import Cleaner
cleaner = Cleaner(
    scripts=True, javascript=True, comments=True,
    style=False, links=False, meta=True,
    page_structure=False, processing_instructions=True,
    embedded=True, frames=True, forms=False,
    annoying_tags=True, remove_tags=None,
    remove_unknown_tags=True, safe_attrs_only=True,
    safe_attrs=frozenset(["href","src","alt","title","class","id"]),
    add_nofollow=False, host_whitelist=(), whitelist_tags=set()
)
clean_html = cleaner.clean_html(html_string)
```

#### HTML diff
```python
from lxml.html.diff import htmldiff, html_annotate
diff = htmldiff(old_html, new_html)
annotated = html_annotate([(html1, "v1"), (html2, "v2")])
```

---

### CSS Selectors

```python
from lxml.cssselect import CSSSelector
sel = CSSSelector("div.main > p.intro")
results = sel(root)                         # list of Elements

# Direct method
root.cssselect("div.main > p.intro")
```

Supported selectors: `*`, `tag`, `.class`, `#id`, `[attr]`, `[attr=val]`, `[attr~=val]`, `[attr|=val]`, `[attr^=val]`, `[attr$=val]`, `[attr*=val]`, `:first-child`, `:last-child`, `:nth-child()`, `:nth-last-child()`, `:nth-of-type()`, `:only-child`, `:only-of-type`, `:empty`, `:not()`, `>`, `+`, `~`, ` ` (descendant)

---

### Parsing Options

```python
parser = etree.XMLParser(
    encoding="utf-8",
    remove_blank_text=True,     # strip ignorable whitespace
    remove_comments=True,
    remove_pis=True,            # processing instructions
    strip_cdata=True,
    resolve_entities=True,
    no_network=True,
    recover=False,              # try to recover from errors
    huge_tree=False             # allow very deep/large trees
)
tree = etree.parse("file.xml", parser)

html_parser = etree.HTMLParser(encoding="utf-8", remove_blank_text=True, remove_comments=True)
tree = etree.parse("file.html", html_parser)
```

#### iterparse (streaming)
```python
for event, elem in etree.iterparse("large.xml", events=("start", "end"), tag="record"):
    if event == "end":
        process(elem)
        elem.clear()                # free memory
        while elem.getprevious() is not None:
            del elem.getparent()[0]
```

#### Feed parser
```python
parser = etree.XMLParser()
parser.feed("<root>")
parser.feed("<child/>")
parser.feed("</root>")
root = parser.close()
```

#### Custom resolvers
```python
class MyResolver(etree.Resolver):
    def resolve(self, system_url, public_id, context):
        return self.resolve_string("<fallback/>", context)
parser = etree.XMLParser()
parser.resolvers.add(MyResolver())
```

---

### Namespace Handling

```python
nsmap = {"ns": "http://example.com/ns", "other": "http://example.com/other"}
root = etree.Element("{http://example.com/ns}root", nsmap=nsmap)
root.xpath("//ns:elem", namespaces=nsmap)
etree.QName("http://example.com/ns", "tag")        # Clark notation helper
etree.QName(elem).localname                         # strip namespace
etree.QName(elem).namespace
```

---

### Custom Element Classes

```python
class MyElement(etree.ElementBase):
    @property
    def name(self):
        return self.get("name")

lookup = etree.ElementNamespaceClassLookup()
namespace = lookup.get_namespace("http://example.com")
namespace["record"] = MyElement

parser = etree.XMLParser()
parser.set_element_class_lookup(lookup)
```

---

### objectify / ObjectPath

```python
from lxml import objectify
root = objectify.fromstring("<root><item>1</item><item>2</item></root>")
root.item                   # first <item>
root.item[1]                # second <item>
int(root.item)              # auto-type (int, float, bool, str)

path = objectify.ObjectPath("root.item")
path(root)                  # navigate
path.setattr(root, "new")  # set value
```

---

### Error Handling / Logging

```python
try:
    root = etree.fromstring(bad_xml)
except etree.XMLSyntaxError as e:
    print(e.error_log)
    for entry in e.error_log:
        print(entry.line, entry.column, entry.message)

# Global log
log = etree.use_global_python_log(etree.PyErrorLog())
```

---

---

## BeautifulSoup4

### Installation
```
pip install beautifulsoup4 lxml html5lib
from bs4 import BeautifulSoup, Comment, SoupStrainer
```

---

### Parsers

| Parser | Install | Speed | Lenient | Use when |
|--------|---------|-------|---------|----------|
| `html.parser` | built-in | moderate | moderate | No extra deps needed |
| `lxml` | `pip install lxml` | fast | yes | Speed matters, well-formed HTML |
| `html5lib` | `pip install html5lib` | slow | very | Must match browser parsing exactly |
| `lxml-xml` / `xml` | `pip install lxml` | fast | no | Parsing XML (not HTML) |

```python
soup = BeautifulSoup(html, "lxml")
soup = BeautifulSoup(html, "html.parser")
soup = BeautifulSoup(html, "html5lib")
soup = BeautifulSoup(xml, "lxml-xml")         # or "xml"
```

---

### Object Types

| Type | Description | Example |
|------|-------------|---------|
| `Tag` | HTML/XML element | `soup.div` |
| `NavigableString` | Text within a tag | `tag.string` |
| `BeautifulSoup` | Whole document | `soup` |
| `Comment` | HTML comment | `<!-- ... -->` |

Also: `CData`, `ProcessingInstruction`, `Declaration`, `Doctype`

---

### Navigation

#### Down
```python
tag.contents          # list of direct children
tag.children          # iterator of direct children
tag.descendants       # recursive iterator of all descendants
tag.string            # single NavigableString child (or None)
tag.strings           # all text strings (generator)
tag.stripped_strings   # stripped text strings (generator)
```

#### Up
```python
tag.parent            # direct parent
tag.parents           # all ancestors (generator)
```

#### Sideways
```python
tag.next_sibling      # next sibling (may be whitespace NavigableString)
tag.previous_sibling  # previous sibling
tag.next_siblings     # all following siblings (generator)
tag.previous_siblings # all preceding siblings (generator)
```

#### Forward/backward in parse order
```python
tag.next_element      # next element in parse order (may enter children)
tag.previous_element  # previous element in parse order
tag.next_elements     # generator forward
tag.previous_elements # generator backward
```

---

### Search Methods

#### find / find_all
```python
soup.find("div")                            # first <div>
soup.find_all("div")                        # all <div>
soup.find("div", class_="main")             # class filter
soup.find("div", id="content")              # id filter
soup.find("div", attrs={"data-id": "5"})    # arbitrary attribute
soup.find_all("div", limit=3)               # max results
soup.find_all(["h1", "h2", "h3"])           # list of tags
soup.find_all(True)                         # all tags
soup.find_all(string="exact text")          # by string content
soup.find_all(string=re.compile("pattern")) # regex on text
soup("div")                                 # shortcut for find_all
tag("p")                                    # find_all within tag
```

#### Filter types
| Type | Example | Matches |
|------|---------|---------|
| String | `"div"` | Tag name exactly |
| Regex | `re.compile("^h[1-6]$")` | Tag names matching regex |
| List | `["h1", "h2"]` | Any tag in list |
| `True` | `True` | Any tag |
| Function | `lambda tag: tag.has_attr("id")` | Custom predicate |

#### Relative search
```python
tag.find_parent("div")                # first matching ancestor
tag.find_parents("div")              # all matching ancestors
tag.find_next_sibling("p")           # next sibling matching
tag.find_next_siblings("p")          # all next siblings matching
tag.find_previous_sibling("p")       # previous sibling matching
tag.find_previous_siblings("p")      # all previous siblings matching
tag.find_next("p")                   # next element in parse order matching
tag.find_all_next("p")              # all following in parse order
tag.find_previous("p")              # previous in parse order
tag.find_all_previous("p")          # all previous in parse order
```

#### CSS selectors
```python
soup.select("div.main > p.intro")        # list of matches
soup.select_one("div.main > p.intro")    # first match
soup.select("div[data-id]")              # attribute presence
soup.select("div[data-id='5']")          # attribute value
soup.select("p:nth-of-type(2)")          # pseudo-selector
soup.select("h1, h2, h3")               # multiple selectors
```

---

### Tree Modification

#### Create
```python
new_tag = soup.new_tag("a", href="http://example.com", class_="link")
new_tag.string = "Click here"
new_string = NavigableString("some text")
```

#### Insert / append
```python
tag.append(new_tag)                  # append child
tag.extend([tag1, tag2])             # append multiple children
tag.insert(0, new_tag)              # insert at position
tag.insert_before(new_tag)          # insert before this tag
tag.insert_after(new_tag)           # insert after this tag
```

#### Remove
```python
tag.clear()                          # remove all children (keep tag)
extracted = tag.extract()            # remove from tree, return it
tag.decompose()                      # remove from tree, destroy it
```

#### Replace / wrap
```python
tag.replace_with(new_tag)           # replace in tree
tag.replace_with("plain text")      # replace with string
tag.wrap(soup.new_tag("div"))       # wrap tag in new parent
tag.unwrap()                        # replace tag with its children
```

#### Smooth
```python
tag.smooth()                         # merge adjacent NavigableStrings
```

---

### Output

#### Serialize
```python
str(soup)                            # full HTML string
soup.prettify()                      # indented HTML string
soup.prettify("utf-8")              # prettified bytes
tag.decode_contents()               # inner HTML (string)
tag.encode_contents()               # inner HTML (bytes)
```

#### Formatters
```python
soup.prettify(formatter="minimal")   # default: encode only necessary chars
soup.prettify(formatter="html")      # HTML entity encoding
soup.prettify(formatter="html5")     # HTML5 void elements (no closing /)
soup.prettify(formatter=None)        # no encoding at all
# Custom formatter
from bs4.formatter import HTMLFormatter
fmt = HTMLFormatter(indent=4, void_element_close_prefix=" /")
soup.prettify(formatter=fmt)
```

#### Text extraction
```python
tag.get_text()                       # all text content
tag.get_text(separator=" ")          # text with separator
tag.get_text(strip=True)            # stripped text
tag.string                           # direct string child (or None)
list(tag.strings)                    # all strings
list(tag.stripped_strings)           # all stripped strings
```

---

### Encoding

#### Unicode, Dammit
```python
from bs4 import UnicodeDammit
dammit = UnicodeDammit(byte_string)
dammit.unicode_markup                # decoded string
dammit.original_encoding            # detected encoding

dammit = UnicodeDammit(byte_string, ["windows-1252", "iso-8859-1"])  # suggest encodings
```

#### Parser encoding
```python
soup = BeautifulSoup(html, "lxml", from_encoding="iso-8859-1")
soup = BeautifulSoup(html, "lxml", exclude_encodings=["ascii"])
```

#### detwingle
```python
from bs4 import UnicodeDammit
fixed = UnicodeDammit.detwingle(byte_string)   # fix mixed UTF-8 + Windows-1252
```

---

### SoupStrainer (Partial Parsing)

Parse only matching elements (faster, less memory):

```python
from bs4 import SoupStrainer
only_links = SoupStrainer("a")
only_main = SoupStrainer(id="main")
only_classes = SoupStrainer(class_="article")
custom = SoupStrainer(lambda name, attrs: name == "div" and "data-id" in attrs)

soup = BeautifulSoup(html, "lxml", parse_only=only_links)
```

---

### Multi-valued Attributes

Some attributes (like `class`) are treated as lists:
```python
tag = soup.find("div", class_="a b")
tag["class"]                  # ["a", "b"] (list)
tag["id"]                     # "main" (string)

# Searching
soup.find_all("div", class_="a")    # matches if "a" is one of the classes
soup.find_all("div", class_="a b")  # matches if both present
```

To disable multi-valued attribute behavior:
```python
soup = BeautifulSoup(html, "lxml", multi_valued_attributes=None)
```

---

### Tag Attributes

```python
tag["href"]                  # get attribute (KeyError if missing)
tag.get("href")             # get attribute (None if missing)
tag.get("href", "default")  # get with default
tag.attrs                    # dict of all attributes
tag["class"] = "new"        # set attribute
del tag["class"]            # delete attribute
tag.has_attr("class")       # check existence
```

### Tag Properties

```python
tag.name                     # tag name ("div", "p", etc.)
tag.name = "span"           # rename tag
```
