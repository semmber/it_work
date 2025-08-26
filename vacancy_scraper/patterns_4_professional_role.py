PATTERNS = {
    "Data Engineer": [
        r"\bdata\s*engineer\b", r"\betl\b",
        r"\bdata\s*platform\b", r"\bspark\b",
        r"\bkafka\b", r"\bairflow\b", r"\bdbt\b",
        r"\bclickhouse\b", r"\bhadoop\b",
        r"\bsnowflake\b"
    ],
    "Go разработчик": [
        r"\bgo\b(?!ogle)",
        r"\bgolang\b"
    ],
    "Python разработчик": [
        r"\bpython\b",
        r"\bpython\s*developer\b",
        r"\bpython-разработчик\b",
        r"\bdjango\b", r"\bfastapi\b",
        r"\bflask\b"
    ],
    "Java разработчик": [
        r"\bjava\b(?!script)",
        r"\bspring\b",
        r"\bspring\s*boot\b"
    ],
    "Frontend разработчик": [
        r"\bfrontend\b", r"\bfront\-end\b", r"\bui\s*developer\b", r"\bui/ux\b",
        r"\breact\b", r"\bvue\b", r"\bangular\b", r"\bsvelte\b",
        r"\bnext\.js\b", r"\bnuxt\.js\b",
        r"\bhtml5?\b", r"\bcss3?\b", r"\bs[ac]ss\b", r"\bless\b",
        r"\bwebpack\b", r"\bvite\b", r"\brollup\b",
        r"\bspa\b", r"\bpwa\b"
    ],
    "JavaScript разработчик": [
        r"\bjavascript\b", r"\becmascript\b", r"\btypescript\b",
        r"\bnode\.?js\b", r"\bnest\.?js\b", r"\bexpress\.?js\b",
        r"\bkoa\b", r"\bfastify\b", r"\bhapi\b",
        r"\bserver[- ]side\b", r"\bbackend\b",
        r"\bnpm\b", r"\byarn\b", r"\bpnpm\b"
    ],
    "Backend разработчик": [
        r"\bbackend\b",
        r"\bback\-end\b",
        r"\bserver\s*side\b",
        r"\brest\b", r"\bgrpc\b",
        r"\bmicroservices?\b"
    ],
    "DevOps / SRE": [
        r"\bdevops\b", r"\bsre\b",
        r"\bplatform\s*engineer\b",
        r"\bkubernetes\b", r"\bk8s\b",
        r"\bterraform\b", r"\bansible\b",
        r"\bci/?cd\b", r"\bdocker\b"
    ],
    "QA / Тестировщик": [
        r"\bqa\b",
        r"\bтестиров(щик|щица)\b",
        r"\bтестиров", r"\bтестировани(е|ю)\b",
        r"\bquality\s*assurance\b",
        r"\bselenium\b", r"\bpytest\b",
        r"\bpostman\b"
    ],
    "Data Scientist / ML Engineer": [
        r"\bdata\s*scientist\b",
        r"\bml\s*engineer\b",
        r"\bmlops\b", r"\bpytorch\b",
        r"\bscikit\-learn\b",
        r"\btensorflow\b",
        r"\bmlflow\b"
    ],
    "Android разработчик": [
        r"\bandroid\b", r"\bkotlin\b",
        r"\bjetpack\b", r"\bcompose\b"
    ],
    "iOS разработчик": [
        r"\bios\b", r"\bswift\b",
        r"\bios\s*developer\b",
        r"\bswiftui\b", r"\bobjective\-c\b"
    ],
    "1C разработчик": [
        r"\b1c\b", r"\b1с\b",
        r"\b1c\s*программист\b",
        r"\bбухгалтерия\b", r"\bупп\b",
        r"\bуправление\s*торговлей\b"
    ]
}