import re

class Token(object):
    Types = {}
    def line(self):
        if hasattr(self,'tokens'):
            return " ".join(self.tokens)
        else:
            return ""

class Meta(Token):
    def __str__(self):
        return "%i: Meta %s" % (self.index, self.name,)

    def __repr__(self):
        return "<%s>" % (str(self),)

class Op(Token):
    Branches = ['if-eq',  'if-ne',  'if-lt',  'if-ge',  'if-gt',  'if-le',
                'if-eqz', 'if-nez', 'if-ltz', 'if-gez', 'if-gtz', 'if-lez',
                'goto']

    def is_branch(self):
        return self.name in Op.Branches

    def __str__(self):
        ret = "%i: Op %s" % (self.index, self.name,)

        if self.size:
            ret += ", size %s" % (self.size,)

        return ret

    def __repr__(self):
        return "<%s>" % (str(self),)

class Label(Token):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return "%i: Label '%s'" % (self.index, self.name,)

    def __repr__(self):
        return "<%s>" % (str(self),)

    def __eq__(self, obj):
        return isinstance(obj, Label) and obj.name == self.name
    
class Parser(object):
    def __init__(self):
        self.plaintext = None
        self.debug = True
        self.labels = {}
        self.comment_pattern = re.compile('#.*$')

    def parse(self, text):
        self.plaintext = str(text)

        text = text.strip()
        text = text.split("\n")

        text = map(lambda x: self.comment_pattern.sub('', x), text)
        text = map(str.strip, text)
        text = filter(lambda x: len(x) > 0, text)

        if self.debug:
            print "%i lines of code" % (len(text),)

        self.tokens = map(self.parse_line, text)
    
    def parse_line(self, line):

        def parse_meta(line):
            line = line[1:] # remove initial .
            tokens = line.split(" ")
            tokens = filter(lambda x: len(x) > 0, tokens)

            name = tokens[0]

            if name in Token.Types:
                kls = Token.Types[name]
            else:
                kls = type(name+"*meta", (Meta,), {'name': name})
                Token.Types[name] = kls

            ret = kls()
            ret.tokens = tokens

            return ret

        def parse_op(line):
            tokens = line.split(" ")
            tokens = filter(lambda x: len(x) > 0, tokens)

            op = tokens[0]
            opname = op
            opsize = None

            if '/' in op:
                op = op.split('/')
                opname = op[0]
                opsize = op[1]

            if opname in Token.Types:
                kls = Token.Types[opname]
            else:
                kls = type(opname, (Op,), {'name': opname})
                Token.Types[opname] = kls
            
            ret = kls()
            ret.size = opsize
            ret.tokens = tokens

            return ret
        
        def parse_label(line):
            label = line[1:]

            ret = Label(label)
            ret.tokens = [line]
            ret.branches = set()

            self.labels[label] = ret

            return ret

        if line[0] == '.':
            return parse_meta(line)
        elif line[0] == ':':
            return parse_label(line)
        else:
            return parse_op(line)

    def analyze(self):
        def split_methods(tokens):
            first_idx = None

            methods = []
            for idx, token in enumerate(tokens):
                if isinstance(token, Meta):
                    if token.name == "method":
                        if first_idx is None:
                            first_idx = idx
                        else:
                            raise ValueError(".method before .endmethod")

                    elif token.name == "end" and token.tokens[-1] == "method":
                        methods.append((first_idx, idx))
                        first_idx = None

            for (start, end) in methods:
                yield tokens[start:end+1]

        def label_branch(op):
            if isinstance(op, Op) and op.is_branch():
                tokens = op.tokens
                jumplabel = tokens[-1]
                jumplabel = jumplabel[1:]
                
                assert jumplabel in self.labels

                label = self.labels[jumplabel]

                op.jumplabel = label
                label.branches += op

            return op

        def label_index((idx, token)):
            token.index = idx
            return token
        
        def token_char(token):
            if isinstance(token, Op):
                if token.is_branch():
                    return "B"
                else:
                    return "O"
            elif isinstance(token, Meta):
                return "M"
            elif isinstance(token, Label):
                return "L"
            else:
                return "U"

        self.tokens = map(label_index, enumerate(self.tokens))
        self.tokens = map(label_branch, self.tokens)
        self.token_list = reduce(lambda x, y: x + token_char(y), self.tokens, "")

    def optimize(self):
        pass

class RewriteRules:
    @staticmethod
    def merge_labels(tokens, start, end):
        assert all((isinstance(x, Label) for x in tokens[start:end+1]))
        

if __name__ == "__main__":
    parser = Parser()
    with open("renderShowUi") as f:
        parser.parse(f.read())
        
        parser.analyze()
        parser.optimize()
        print parser.token_list

