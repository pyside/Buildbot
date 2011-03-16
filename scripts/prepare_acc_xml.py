#!/usr/bin/python

import sys
from string import Template

module_name = sys.argv[1]
ref_base_dir = sys.argv[2]
new_base_dir = '/usr' if len(sys.argv) < 4 else sys.argv[3]

f = open('/tmp/%s-acc.xml.in' % module_name, 'r')
template = Template(f.read())
f.close()

f = open('/tmp/%s-acc-ref.xml' % module_name, 'w')
contents = template.substitute(VERSION_DESCRIPTION='reference',
                               BASE_DIR=ref_base_dir)
f.write(contents)
f.close()

f = open('/tmp/%s-acc-new.xml' % module_name, 'w')
contents = template.substitute(VERSION_DESCRIPTION='new',
                               BASE_DIR=new_base_dir)
f.write(contents)
f.close()

