import json
import tutils
from six.moves import cStringIO
import libpathod.pathoc as pathoc
import libpathod


class _TestDaemon:
    @classmethod
    def setUpAll(self):
        self.d = libpathoc.test.Daemon(
            ssl=self.ssl,
            staticdir=tutils.test_data.path("data"),
            anchors=[("/anchor/.*", "202")]
        )

    @classmethod
    def tearDownAll(self):
        self.d.shutdown()

    def setUp(self):
        self.d.clear_log()

    def test_info(self):
        c = pathoc.Pathoc(
            "127.0.0.1",
            self.d.port,
            ssl = self.ssl
        )
        c.connect()
        _, _, _, _, content = c.request("get:/api/info")
        assert tuple(json.loads(content)["version"]) == libpathoc.version.IVERSION


class TestDaemonSSL(_TestDaemon):
    ssl = True
    def test_sni(self):
        c = pathoc.Pathoc(
            "127.0.0.1",
            self.d.port,
            ssl = True,
            sni = "foobar.com"
        )
        c.connect()
        c.request("get:/p/200")
        _, _, _, _, content = c.request("get:/api/log")
        d = json.loads(content)
        assert d["log"][0]["request"]["sni"] == "foobar.com"


class TestDaemon(_TestDaemon):
    ssl = False
    def tval(self, requests, showreq=False, showresp=False, explain=False, hexdump=False, timeout=None, ignorecodes=None, ignoretimeout=None):
        c = pathoc.Pathoc("127.0.0.1", self.d.port)
        c.connect()
        if timeout:
            c.settimeout(timeout)
        s = cStringIO.StringIO()
        for i in requests:
            c.print_request(
                i,
                showreq = showreq,
                showresp = showresp,
                explain = explain,
                hexdump = hexdump,
                ignorecodes = ignorecodes,
                ignoretimeout = ignoretimeout,
                fp = s
            )
        return s.getvalue()

    def test_ssl_error(self):
        c = pathoc.Pathoc("127.0.0.1", self.d.port, ssl = True)
        tutils.raises("ssl handshake", c.connect)

    def test_ignorecodes(self):
        assert "200" in self.tval(["get:'/p/200:b@1'"])
        assert "200" not in self.tval(["get:'/p/200:b@1'"], ignorecodes=[200])
        assert "200" not in self.tval(["get:'/p/200:b@1'"], ignorecodes=[200, 201])
        assert "202" in self.tval(["get:'/p/202:b@1'"], ignorecodes=[200, 201])

    def test_timeout(self):
        assert "Timeout" in self.tval(["get:'/p/200:p0,10'"], timeout=0.01)
        assert "HTTP" in self.tval(["get:'/p/200:p5,10'"], showresp=True, timeout=0.01)
        assert not "HTTP" in self.tval(["get:'/p/200:p5,10'"], showresp=True, timeout=0.01, ignoretimeout=True)

    def test_showresp(self):
        reqs = [ "get:/api/info:p0,0", "get:/api/info:p0,0" ]
        assert self.tval(reqs).count("200") == 2
        assert self.tval(reqs, showresp=True).count("unprintables escaped") == 2
        assert self.tval(reqs, showresp=True, hexdump=True).count("hex dump") == 2

    def test_showresp_httperr(self):
        v = self.tval(["get:'/p/200:d20'"], showresp=True)
        assert "Invalid headers" in v
        assert "HTTP/" in v

    def test_explain(self):
        reqs = [ "get:/p/200:b@100" ]
        assert not "b@100" in self.tval(reqs, explain=True)

    def test_showreq(self):
        reqs = [ "get:/api/info:p0,0", "get:/api/info:p0,0" ]
        assert self.tval(reqs, showreq=True).count("unprintables escaped") == 2
        assert self.tval(reqs, showreq=True, hexdump=True).count("hex dump") == 2

    def test_parse_err(self):
        assert "Error parsing" in self.tval(["foo"])

    def test_conn_err(self):
        assert "Invalid server response" in self.tval(["get:'/p/200:d2'"])

    def test_fileread(self):
        d = tutils.test_data.path("data/request")
        assert "foo" in self.tval(["+%s"%d], showreq=True)
        assert "File" in self.tval(["+/nonexistent"])

