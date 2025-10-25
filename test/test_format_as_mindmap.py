import sys
import os
import json

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入要测试的函数
from libs.rag_base.graphs.graph_defs import format_as_mindmap


class MockComments:
    """模拟评论对象，用于测试"""
    def __init__(self, overall_evaluation=None, specific_issues=None, 
                 improvement_suggestions=None, code_examples=None):
        self.overall_evaluation = overall_evaluation or "测试总体评价"
        self.specific_issues = specific_issues or []
        self.improvement_suggestions = improvement_suggestions or []
        self.code_examples = code_examples or []


def test_format_as_mindmap():
    """测试format_as_mindmap函数在各种情况下的行为"""
    
    print("开始测试 format_as_mindmap 函数...")
    print("=" * 60)
    
    # 测试用例1: JSON字符串格式的代码示例（用户提供的实际案例）
    print("\n测试用例1: JSON字符串格式的代码示例")
    print("-" * 60)
    
    json_string_example = '["# Improved approach using dynamic device checking\\n{%- if sonic_asic_platform == \\"nvidia-bluefield\\" %}\\n{%- if docker_container_name == \\"pmon\\" %}\\n$(if [ -e \\"/dev/nvme0\\" ]; then echo \\"--device=/dev/nvme0:/dev/nvme0\\"; fi) \\\\\\n{%- endif %}\\n{%- endif %}", "# Alternative approach with loop for multiple NVMe devices\\n{%- if sonic_asic_platform == \\"nvidia-bluefield\\" %}\\n{%- if docker_container_name == \\"pmon\\" %}\\n$(for nvme_dev in /dev/nvme*; do if [ -e \\"$nvme_dev\\" ]; then echo \\"--device=$nvme_dev:$nvme_dev\\"; fi; done) \\\\\\n{%- endif %}\\n{%- endif %}"]'
    comments1 = MockComments(
        code_examples=[json_string_example]
    )
    
    result1 = format_as_mindmap(comments1)
    print(result1)

    print("\n测试用例1完成")
    
    # 测试用例2: 普通字符串形式的代码示例
    print("\n测试用例2: 普通字符串形式的代码示例")
    print("-" * 60)
    
    normal_example = "# 这是一个普通的Python示例\nprint('Hello, World!')\nfor i in range(5):\n    print(i)"
    
    comments2 = MockComments(
        code_examples=[normal_example]
    )
    
    result2 = format_as_mindmap(comments2)
    print(result2)
    print("\n测试用例2完成")
    
    # 测试用例3: 混合类型的代码示例
    print("\n测试用例3: 混合类型的代码示例")
    print("-" * 60)
    
    mixed_examples = [
        json_string_example,  # JSON字符串
        "# 简单Python函数\ndef add(a, b):\n    return a + b",  # 普通字符串
        {"不是": "字符串对象"}  # 非字符串对象
    ]
    
    comments3 = MockComments(
        code_examples=mixed_examples
    )
    
    result3 = format_as_mindmap(comments3)
    print(result3)
    print("\n测试用例3完成")
    
    # 测试用例4: 不包含#开头描述的代码示例
    print("\n测试用例4: 不包含#开头描述的代码示例")
    print("-" * 60)
    
    no_comment_example = "def multiply(x, y):\n    return x * y\n\nresult = multiply(3, 4)\nprint(result)"
    
    comments4 = MockComments(
        code_examples=[no_comment_example]
    )
    
    result4 = format_as_mindmap(comments4)
    print(result4)
    print("\n测试用例4完成")
    
    # 测试用例5: 空的代码示例
    print("\n测试用例5: 空的代码示例")
    print("-" * 60)
    
    comments5 = MockComments(
        code_examples=[]
    )
    
    result5 = format_as_mindmap(comments5)
    print(result5)
    print("\n测试用例5完成")
    
    print("\n" + "=" * 60)
    print("所有测试用例执行完成！")
    
    # 测试用例6: Bash脚本识别测试
    print("\n测试用例6: Bash脚本识别测试")
    print("-" * 60)
    
    bash_examples = [
        # 测试带shebang的bash脚本
        "#!/bin/bash\n# 这是一个bash脚本示例\necho \"Hello, World!\"\nfor i in {1..5}; do\n    echo $i\ndone",
        # 测试没有shebang但有bash特征的代码
        "# 简单bash命令\nif [ -f \"config.txt\" ]; then\n    echo \"配置文件存在\"\n    cat config.txt\nfi",
        # 测试变量引用和命令替换
        "# Bash变量和命令替换\nDIR=\"/tmp\"\nFILES=$(ls -la $DIR)\nexport PATH=$PATH:/usr/local/bin"
    ]
    
    comments6 = MockComments(
        code_examples=bash_examples
    )
    
    result6 = format_as_mindmap(comments6)
    print(result6)
    print("\n测试用例6完成")
    
    # 测试用例7: C语言识别测试
    print("\n测试用例7: C语言识别测试")
    print("-" * 60)
    
    c_examples = [
        "#include <stdio.h>\n\nint main() {\n    printf(\"Hello, World!\\n\");\n    return 0;\n}",
        "/* C语言函数示例 */\nvoid print_number(int num) {\n    printf(\"Number: %d\\n\", num);\n}"
    ]
    
    comments7 = MockComments(
        code_examples=c_examples
    )
    
    result7 = format_as_mindmap(comments7)
    print(result7)
    print("\n测试用例7完成")
    
    # 测试用例8: C++语言识别测试
    print("\n测试用例8: C++语言识别测试")
    print("-" * 60)
    
    cpp_examples = [
        "#include <iostream>\nusing namespace std;\n\nint main() {\n    cout << \"Hello, World!\" << endl;\n    return 0;\n}",
        "# C++类示例\nclass Person {\npublic:\n    string name;\n    void greet() {\n        cout << \"Hello, \" << name << endl;\n    }\n}"
    ]
    
    comments8 = MockComments(
        code_examples=cpp_examples
    )
    
    result8 = format_as_mindmap(comments8)
    print(result8)
    print("\n测试用例8完成")
    
    bash_example = '["```bash\\nmanage_gnmi_cert_entry() {\\n    local operation=$1\\n    local cname=$2\\n    \\n    # Validate input\\n    if [[ ! \\"$cname\\" =~ ^[a-zA-Z0-9_.-]+$ ]]; then\\n   echo \\"Invalid TELEMETRY_CLIENT_CNAME: $cname\\" >&2\\n        return 1\\n    fi\\n    \\n    local key=\\"GNMI_CLIENT_CERT|$cname\\"\\n    \\n    nsenter --target 1 --pid --mount --uts --ipc --net bash -c \\"\\n        if [ \\\\\\"$operation\\\\\\" = \\\\\\"create\\\\\\" ]; then\\n            CURRENT_ENTRY=\\\\$(sonic-db-cli CONFIG_DB HGETALL \\\\\\"$key\\\\\\")\\n            if [ -z \\\\\\"\\\\$CURRENT_ENTRY\\\\\\" ]; then\\n                echo \\\\\\"Creating $key entry in CONFIG_DB\\\\\\"\\n                RESULT=\\\\$(sonic-db-cli CONFIG_DB HSET \\\\\\"$key\\\\\\" role \\\\\\"gnmi_read\\\\\\" 2>&1)\\n              if [ \\\\$? -ne 0 ]; then\\n                    echo \\\\\\"Error creating entry: $RESULT\\\\\\" >&2\\n             exit 1\\n                fi\\n                echo \\\\\\"sonic-db-cli HSET result: $RESULT\\\\\\"\\n  else\\n                echo \\\\\\"$key already exists in CONFIG_DB\\\\\\"\\n            fi\\n        else\\n            CURRENT_ENTRY=\\\\$(sonic-db-cli CONFIG_DB HGETALL \\\\\\"$key\\\\\\")\\n            if [ -n \\\\\\"\\\\$CURRENT_ENTRY\\\\\\" ]; then\\n                echo \\\\\\"Removing $key entry from CONFIG_DB\\\\\\"\\n                RESULT=\\\\$(sonic-db-cli CONFIG_DB DEL \\\\\\"$key\\\\\\" 2>&1)\\n                if [ \\\\$? -ne 0 ]; then\\n                    echo \\\\\\"Errorremoving entry: $RESULT\\\\\\" >&2\\n                    exit 1\\n                fi\\n                echo \\\\\\"sonic-db-cli DEL result: $RESULT\\\\\\"\\n            else\\n                echo \\\\\\"No $key entry exists, nothing to remove\\\\\\"\\n            fi\\n        fi\\n    \\"\\n}\\n\\nif [ -n \\"${TELEMETRY_CLIENT_CNAME}\\" ]; then\\n    if [ \\"${TELEMETRY_CLIENT_CERT_VERIFY_ENABLED}\\" = \\"true\\" ]; then\\n        manage_gnmi_cert_entry \\"create\\" \\"$TELEMETRY_CLIENT_CNAME\\"\\n    else\\n        manage_gnmi_cert_entry \\"delete\\" \\"$TELEMETRY_CLIENT_CNAME\\"\\n    fi\\nelse\\n    echo \\"TELEMETRY_CLIENT_CNAME not set, skipping CONFIG_DB update/cleanup\\"\\nfi\\n```"]'

    comments9 = MockComments(
        code_examples=[bash_example]
    )
    
    result9 = format_as_mindmap(comments9)
    print(result9)
    print("\n测试用例9完成")

    bash_example10 = '["#!/usr/bin/env bash\\n\\n## Populate or remove GNMI client cert entry based on TELEMETRY_CLIENT_CERT_VERIFY_ENABLED\\nhandle_config_db_entry() {\\n    local action=$1\\n    nsenter --target 1 --pid --mount --uts --ipc --net env TELEMETRY_CLIENT_CNAME=\\"$TELEMETRY_CLIENT_CNAME\\" bash -c \\"\\n  cname=\\\\\\"$TELEMETRY_CLIENT_CNAME\\\\\\"\\n        key=\\\\\\"GNMI_CLIENT_CERT|\\\\\\${cname}\\\\\\"\\n        if [ \\\\\\"$action\\\\\\" = \\\\\\"create\\\\\\" ]; then\\n            CURRENT_ENTRY=$(sonic-db-cli CONFIG_DB HGETALL \\\\\\"$key\\\\\\")\\n            if [ -z \\\\\\"$CURRENT_ENTRY\\\\\\" ]; then\\n                echo \\\\\\"Creating $key entry in CONFIG_DB\\\\\\"\\n                RESULT=$(sonic-db-cli CONFIG_DB HSET \\\\\\"$key\\\\\\" role \\\\\\"gnmi_read\\\\\\")\\n          if [ $? -ne 0 ]; then\\n                    echo \\\\\\"Failed to create $key entry in CONFIG_DB\\\\\\" >&2\\n                exit 1\\n                fi\\n                echo \\\\\\"sonic-db-cli HSET result: $RESULT\\\\\\"\\n     else\\n                echo \\\\\\"$key already exists in CONFIG_DB\\\\\\"\\n            fi\\n        else\\n  CURRENT_ENTRY=$(sonic-db-cli CONFIG_DB HGETALL \\\\\\"$key\\\\\\")\\n            if [ -n \\\\\\"$CURRENT_ENTRY\\\\\\" ]; then\\n                echo \\\\\\"Removing $key entry from CONFIG_DB\\\\\\"\\n                RESULT=$(sonic-db-cli CONFIG_DB DEL \\\\\\"$key\\\\\\")\\n                if [ $? -ne 0 ]; then\\n                    echo \\\\\\"Failed to remove $key entry from CONFIG_DB\\\\\\" >&2\\n                    exit 1\\n                fi\\n                echo \\\\\\"sonic-db-cli DEL result: $RESULT\\\\\\"\\n            else\\n                echo \\\\\\"No $key entry exists, nothing to remove\\\\\\"\\n            fi\\n        fi\\n    \\"\\n}\\n\\nif [ -n \\"${TELEMETRY_CLIENT_CNAME}\\" ]; then\\n    # Optional: Add validation for TELEMETRY_CLIENT_CNAME format\\n    # if ! [[ \\"${TELEMETRY_CLIENT_CNAME}\\" =~ ^[a-zA-Z0-9_]+$ ]]; then\\n    #  echo \\"Invalid TELEMETRY_CLIENT_CNAME format\\" >&2\\n    #     exit 1\\n    # fi\\n    if [ \\"${TELEMETRY_CLIENT_CERT_VERIFY_ENABLED}\\" = \\"true\\" ]; then\\n        handle_config_db_entry \\"create\\"\\n    else\\n        handle_config_db_entry \\"remove\\"\\n    fi\\nelse\\n    if [ \\"${TELEMETRY_CLIENT_CERT_VERIFY_ENABLED}\\" = \\"true\\" ]; then\\n        echo \\"TELEMETRY_CLIENT_CNAME not set, skipping CONFIG_DB update\\"\\n    else\\n        echo \\"TELEMETRY_CLIENT_CNAME not set, skipping CONFIG_DB cleanup\\"\\n    fi\\nfi\\n\\n## Populate serial number to StateDB so telemetry could use it\\n## Only update if decode-syseeprom succeeds and value differs from Redis\\n## Set TELEMETRY_WATCHDOG_SERIALNUMBER_PROBE_ENABLED=true to enable"]'
    bash_example10 = '["#!/usr/bin/env bash\\n\\n## Populate or remove GNMI client cert entry based on TELEMETRY_CLIENT_CERT_VERIFY_ENABLED\\nhandle_config_db_entry() {\\n    local action=$1\\n    nsenter --target 1 --pid --mount --uts --ipc --net env TELEMETRY_CLIENT_CNAME=\\\"$TELEMETRY_CLIENT_CNAME\\\" bash -c \\\"\\n  cname=\\\\\\\"$TELEMETRY_CLIENT_CNAME\\\\\\\"\\n        key=\\\\\\\"GNMI_CLIENT_CERT|\\\\\\${cname}\\\\\\\"\\n        if [ \\\\\\\"$action\\\\\\\" = \\\\\\\"create\\\\\\\" ]; then\\n            CURRENT_ENTRY=$(sonic-db-cli CONFIG_DB HGETALL \\\\\\\"$key\\\\\\\")\\n            if [ -z \\\\\\\"$CURRENT_ENTRY\\\\\\\" ]; then\\n                echo \\\\\\\"Creating $key entry in CONFIG_DB\\\\\\\"\\n                RESULT=$(sonic-db-cli CONFIG_DB HSET \\\\\\\"$key\\\\\\\" role \\\\\\\"gnmi_read\\\\\\\")\\n          if [ $? -ne 0 ]; then\\n                    echo \\\\\\\"Failed to create $key entry in CONFIG_DB\\\\\\\" >&2\\n                exit 1\\n                fi\\n                echo \\\\\\\"sonic-db-cli HSET result: $RESULT\\\\\\\"\\n     else\\n                echo \\\\\\\"$key already exists in CONFIG_DB\\\\\\\"\\n            fi\\n        else\\n  CURRENT_ENTRY=$(sonic-db-cli CONFIG_DB HGETALL \\\\\\\"$key\\\\\\\")\\n            if [ -n \\\\\\\"$CURRENT_ENTRY\\\\\\\" ]; then\\n                echo \\\\\\\"Removing $key entry from CONFIG_DB\\\\\\\"\\n                RESULT=$(sonic-db-cli CONFIG_DB DEL \\\\\\\"$key\\\\\\\")\\n                if [ $? -ne 0 ]; then\\n                    echo \\\\\\\"Failed to remove $key entry from CONFIG_DB\\\\\\\" >&2\\n                    exit 1\\n                fi\\n                echo \\\\\\\"sonic-db-cli DEL result: $RESULT\\\\\\\"\\n            else\\n                echo \\\\\\\"No $key entry exists, nothing to remove\\\\\\\"\\n            fi\\n        fi\\n    \\\"\\n}\\n\\nif [ -n \\\"{TELEMETRY_CLIENT_CNAME}\\\" ]; then\\n    # Optional: Add validation for TELEMETRY_CLIENT_CNAME format\\n    # if ! [[ \\\"{TELEMETRY_CLIENT_CNAME}\\\" =~ ^[a-zA-Z0-9_]+$ ]]; then\\n    #  echo \\\"Invalid TELEMETRY_CLIENT_CNAME format\\\" >&2\\n    #     exit 1\\n    # fi\\n    if [ \\\"{TELEMETRY_CLIENT_CERT_VERIFY_ENABLED}\\\" = \\\"true\\\" ]; then\\n        handle_config_db_entry \\\"create\\\"\\n    else\\n        handle_config_db_entry \\\"remove\\\"\\n    fi\\nelse\\n    if [ \\\"{TELEMETRY_CLIENT_CERT_VERIFY_ENABLED}\\\" = \\\"true\\\" ]; then\\n        echo \\\"TELEMETRY_CLIENT_CNAME not set, skipping CONFIG_DB update\\\"\\n    else\\n        echo \\\"TELEMETRY_CLIENT_CNAME not set, skipping CONFIG_DB cleanup\\\"\\n    fi\\nfi\\n\\n## Populate serial number to StateDB so telemetry could use it\\n## Only update if decode-syseeprom succeeds and value differs from Redis\\n## Set TELEMETRY_WATCHDOG_SERIALNUMBER_PROBE_ENABLED=true to enable"]'
    bash_example10 = '["#!/usr/bin/env bash\n\n## Populate or remove GNMI client cert entry based on TELEMETRY_CLIENT_CERT_VERIFY_ENABLED\nhandle_config_db_entry() {\n    local action=$1\n    nsenter --target 1 --pid --mount --uts --ipc --net env TELEMETRY_CLIENT_CNAME=\"$TELEMETRY_CLIENT_CNAME\" bash -c \"\n  cname=\"$TELEMETRY_CLIENT_CNAME\"\n        key=\"GNMI_CLIENT_CERT|\\${cname}\"\n        if [ \"$action\" = \"create\" ]; then\n            CURRENT_ENTRY=$(sonic-db-cli CONFIG_DB HGETALL \"$key\")\n            if [ -z \"$CURRENT_ENTRY\" ]; then\n                echo \"Creating $key entry in CONFIG_DB\"\n                RESULT=$(sonic-db-cli CONFIG_DB HSET \"$key\" role \"gnmi_read\")\n          if [ $? -ne 0 ]; then\n                    echo \"Failed to create $key entry in CONFIG_DB\" >&2\n                exit 1\n                fi\n                echo \"sonic-db-cli HSET result: $RESULT\"\n     else\n                echo \"$key already exists in CONFIG_DB\"\n            fi\n        else\n  CURRENT_ENTRY=$(sonic-db-cli CONFIG_DB HGETALL \"$key\")\n            if [ -n \"$CURRENT_ENTRY\" ]; then\n                echo \"Removing $key entry from CONFIG_DB\"\n                RESULT=$(sonic-db-cli CONFIG_DB DEL \"$key\")\n                if [ $? -ne 0 ]; then\n                    echo \"Failed to remove $key entry from CONFIG_DB\" >&2\n                    exit 1\n                fi\n                echo \"sonic-db-cli DEL result: $RESULT\"\n            else\n                echo \"No $key entry exists, nothing to remove\"\n            fi\n        fi\n    \"\n}\n\nif [ -n \"{TELEMETRY_CLIENT_CNAME}\" ]; then\n    # Optional: Add validation for TELEMETRY_CLIENT_CNAME format\n    # if ! [[ \"{TELEMETRY_CLIENT_CNAME}\" =~ ^[a-zA-Z0-9_]+$ ]]; then\n    #  echo \"Invalid TELEMETRY_CLIENT_CNAME format\" >&2\n    #     exit 1\n    # fi\n    if [ \"{TELEMETRY_CLIENT_CERT_VERIFY_ENABLED}\" = \"true\" ]; then\n        handle_config_db_entry \"create\"\n    else\n        handle_config_db_entry \"remove\"\n    fi\nelse\n    if [ \"{TELEMETRY_CLIENT_CERT_VERIFY_ENABLED}\" = \"true\" ]; then\n        echo \"TELEMETRY_CLIENT_CNAME not set, skipping CONFIG_DB update\"\n    else\n        echo \"TELEMETRY_CLIENT_CNAME not set, skipping CONFIG_DB cleanup\"\n    fi\nfi\n\n## Populate serial number to StateDB so telemetry could use it\n## Only update if decode-syseeprom succeeds and value differs from Redis\n## Set TELEMETRY_WATCHDOG_SERIALNUMBER_PROBE_ENABLED=true to enable"]'
    bash_example10 = '["#!/usr/bin/env bash\\n\\n## Populate or remove GNMI client cert entry based on TELEMETRY_CLIENT_CERT_VERIFY_ENABLED\\nhandle_config_db_entry() {\\n    local action=$1\\n    nsenter --target 1 --pid --mount --uts --ipc --net env TELEMETRY_CLIENT_CNAME=\\"$TELEMETRY_CLIENT_CNAME\\" bash -c \\"\\n  cname=\\\\\\"$TELEMETRY_CLIENT_CNAME\\\\\\"\\n        key=\\\\\\"GNMI_CLIENT_CERT|\\\\\\\\${cname}\\\\\\\\\\"\\n        if [ \\\\\\"$action\\\\\\" = \\\\\\"create\\\\\\" ]; then\\n            CURRENT_ENTRY=$(sonic-db-cli CONFIG_DB HGETALL \\\\\\"$key\\\\\\")\\n            if [ -z \\\\\\"$CURRENT_ENTRY\\\\\\" ]; then\\n                echo \\\\\\"Creating $key entry in CONFIG_DB\\\\\\"\\n                RESULT=$(sonic-db-cli CONFIG_DB HSET \\\\\\"$key\\\\\\" role \\\\\\"gnmi_read\\\\\\")\\n          if [ $? -ne 0 ]; then\\n                    echo \\\\\\"Failed to create $key entry in CONFIG_DB\\\\\\" >&2\\n                exit 1\\n                fi\\n                echo \\\\\\"sonic-db-cli HSET result: $RESULT\\\\\\"\\n     else\\n                echo \\\\\\"$key already exists in CONFIG_DB\\\\\\"\\n            fi\\n        else\\n  CURRENT_ENTRY=$(sonic-db-cli CONFIG_DB HGETALL \\\\\\"$key\\\\\\")\\n            if [ -n \\\\\\"$CURRENT_ENTRY\\\\\\" ]; then\\n                echo \\\\\\"Removing $key entry from CONFIG_DB\\\\\\"\\n                RESULT=$(sonic-db-cli CONFIG_DB DEL \\\\\\"$key\\\\\\")\\n                if [ $? -ne 0 ]; then\\n                    echo \\\\\\"Failed to remove $key entry from CONFIG_DB\\\\\\" >&2\\n                    exit 1\\n                fi\\n                echo \\\\\\"sonic-db-cli DEL result: $RESULT\\\\\\"\\n            else\\n                echo \\\\\\"No $key entry exists, nothing to remove\\\\\\"\\n            fi\\n        fi\\n    \\"\\n}\\n\\nif [ -n \\"${TELEMETRY_CLIENT_CNAME}\\" ]; then\\n    # Optional: Add validation for TELEMETRY_CLIENT_CNAME format\\n    # if ! [[ \\"${TELEMETRY_CLIENT_CNAME}\\" =~ ^[a-zA-Z0-9_]+$ ]]; then\\n    #  echo \\"Invalid TELEMETRY_CLIENT_CNAME format\\" >&2\\n    #     exit 1\\n    # fi\\n    if [ \\"${TELEMETRY_CLIENT_CERT_VERIFY_ENABLED}\\" = \\"true\\" ]; then\\n        handle_config_db_entry \\"create\\"\\n    else\\n        handle_config_db_entry \\"remove\\"\\n    fi\\nelse\\n    if [ \\"${TELEMETRY_CLIENT_CERT_VERIFY_ENABLED}\\" = \\"true\\" ]; then\\n        echo \\"TELEMETRY_CLIENT_CNAME not set, skipping CONFIG_DB update\\"\\n    else\\n        echo \\"TELEMETRY_CLIENT_CNAME not set, skipping CONFIG_DB cleanup\\"\\n    fi\\nfi\\n\\n## Populate serial number to StateDB so telemetry could use it\\n## Only update if decode-syseeprom succeeds and value differs from Redis\\n## Set TELEMETRY_WATCHDOG_SERIALNUMBER_PROBE_ENABLED=true to enable"]'
    bash_example10 = '["#!/usr/bin/env bash\\n\\n## Populate or remove GNMI client cert entry based on TELEMETRY_CLIENT_CERT_VERIFY_ENABLED\\nhandle_config_db_entry() {\\n    local action=$1\\n    nsenter --target 1 --pid --mount --uts --ipc --net env TELEMETRY_CLIENT_CNAME=\\"$TELEMETRY_CLIENT_CNAME\\" bash -c \\"\\n  cname=\\\\\\"$TELEMETRY_CLIENT_CNAME\\\\\\"\\n        key=\\\\\\"GNMI_CLIENT_CERT|\\\\\\\\${cname}\\\\\\"\\n        if [ \\\\\\"$action\\\\\\" = \\\\\\"create\\\\\\" ]; then\\n            CURRENT_ENTRY=$(sonic-db-cli CONFIG_DB HGETALL \\\\\\"$key\\\\\\")\\n            if [ -z \\\\\\"$CURRENT_ENTRY\\\\\\" ]; then\\n                echo \\\\\\"Creating $key entry in CONFIG_DB\\\\\\"\\n                RESULT=$(sonic-db-cli CONFIG_DB HSET \\\\\\"$key\\\\\\" role \\\\\\"gnmi_read\\\\\\")\\n          if [ $? -ne 0 ]; then\\n                    echo \\\\\\"Failed to create $key entry in CONFIG_DB\\\\\\" >&2\\n                exit 1\\n                fi\\n                echo \\\\\\"sonic-db-cli HSET result: $RESULT\\\\\\"\\n     else\\n                echo \\\\\\"$key already exists in CONFIG_DB\\\\\\"\\n            fi\\n        else\\n  CURRENT_ENTRY=$(sonic-db-cli CONFIG_DB HGETALL \\\\\\"$key\\\\\\")\\n            if [ -n \\\\\\"$CURRENT_ENTRY\\\\\\" ]; then\\n                echo \\\\\\"Removing $key entry from CONFIG_DB\\\\\\"\\n                RESULT=$(sonic-db-cli CONFIG_DB DEL \\\\\\"$key\\\\\\")\\n                if [ $? -ne 0 ]; then\\n                    echo \\\\\\"Failed to remove $key entry from CONFIG_DB\\\\\\" >&2\\n                    exit 1\\n                fi\\n                echo \\\\\\"sonic-db-cli DEL result: $RESULT\\\\\\"\\n            else\\n                echo \\\\\\"No $key entry exists, nothing to remove\\\\\\"\\n            fi\\n        fi\\n    \\"\\n}\\n\\nif [ -n \\"${TELEMETRY_CLIENT_CNAME}\\" ]; then\\n    # Optional: Add validation for TELEMETRY_CLIENT_CNAME format\\n    # if ! [[ \\"${TELEMETRY_CLIENT_CNAME}\\" =~ ^[a-zA-Z0-9_]+$ ]]; then\\n    #  echo \\"Invalid TELEMETRY_CLIENT_CNAME format\\" >&2\\n    #     exit 1\\n    # fi\\n    if [ \\"${TELEMETRY_CLIENT_CERT_VERIFY_ENABLED}\\" = \\"true\\" ]; then\\n        handle_config_db_entry \\"create\\"\\n    else\\n        handle_config_db_entry \\"remove\\"\\n    fi\\nelse\\n    if [ \\"${TELEMETRY_CLIENT_CERT_VERIFY_ENABLED}\\" = \\"true\\" ]; then\\n        echo \\"TELEMETRY_CLIENT_CNAME not set, skipping CONFIG_DB update\\"\\n    else\\n        echo \\"TELEMETRY_CLIENT_CNAME not set, skipping CONFIG_DB cleanup\\"\\n    fi\\nfi\\n\\n## Populate serial number to StateDB so telemetry could use it\\n## Only update if decode-syseeprom succeeds and value differs from Redis\\n## Set TELEMETRY_WATCHDOG_SERIALNUMBER_PROBE_ENABLED=true to enable"]'
    #bash_example10 = '["```bash\\n#!/usr/bin/env bash\\n\\nmanage_gnmi_cert_entry() {\\n    local action=$1\\n    local cname=$2\\n    \\n    nsenter --target 1 --pid --mount --uts --ipc --net bash -c\\"\\n        key=\\\\\\"GNMI_CLIENT_CERT|\\\\\\${TELEMETRY_CLIENT_CNAME}\\\\\\"\\n        if [ \\\\\\"$action\\\\\\" = \\\\\\"create\\\\\\" ]; then\\n            CURRENT_ENTRY=\\\\\\$(sonic-db-cli CONFIG_DB HGETALL \\\\\\"\\\\\\$key\\\\\\")\\n        if [ -z \\\\\\"\\\\\\$CURRENT_ENTRY\\\\\\" ]; then\\n                echo \\\\\\"Creating \\\\\\$key entry in CONFIG_DB\\\\\\"\\n                RESULT=\\\\\\$(sonic-db-cli CONFIG_DB HSET \\\\\\"\\\\\\$key\\\\\\" role \\\\\\"gnmi_read\\\\\\" 2>&1)\\n                if [ \\\\$? -ne 0 ]; then\\n                    echo \\\\\\"Error creating entry: \\\\\\$RESULT\\\\\\" >&2\\n                    exit 1\\n                fi\\n                echo \\\\\\"sonic-db-cli HSET result: \\\\\\$RESULT\\\\\\"\\n            else\\n                echo \\\\\\"\\\\\\$key already exists in CONFIG_DB\\\\\\"\\n            fi\\n        else\\n            CURRENT_ENTRY=\\\\\\$(sonic-db-cli CONFIG_DB HGETALL \\\\\\"\\\\\\$key\\\\\\")\\n            if [ -n \\\\\\"\\\\\\$CURRENT_ENTRY\\\\\\" ]; then\\n                echo \\\\\\"Removing \\\\\\$key entry from CONFIG_DB\\\\\\"\\n                RESULT=\\\\\\$(sonic-db-cli CONFIG_DB DEL \\\\\\"\\\\\\$key\\\\\\" 2>&1)\\n                if [ \\\\$?-ne 0 ]; then\\n                    echo \\\\\\"Error removing entry: \\\\\\$RESULT\\\\\\" >&2\\n                    exit 1\\n                fi\\n                echo \\\\\\"sonic-db-cli DEL result: \\\\\\$RESULT\\\\\\"\\n            else\\n          echo \\\\\\"No \\\\\\$key entry exists, nothing to remove\\\\\\"\\n            fi\\n        fi\\n    \\"\\n}\\n\\n## Populate or remove GNMI client cert entry based on TELEMETRY_CLIENT_CERT_VERIFY_ENABLED\\nif [ -n \\"\\${TELEMETRY_CLIENT_CNAME}\\" ]; then\\n    if [ \\"\\${TELEMETRY_CLIENT_CERT_VERIFY_ENABLED}\\" = \\"true\\" ]; then\\n        manage_gnmi_cert_entry \\"create\\" \\"\\${TELEMETRY_CLIENT_CNAME}\\"\\n    else\\n        manage_gnmi_cert_entry \\"delete\\" \\"\\${TELEMETRY_CLIENT_CNAME}\\"\\n    fi\\nelse\\n    echo \\"TELEMETRY_CLIENT_CNAME not set, skipping CONFIG_DB update/cleanup\\"\\nfi\\n```"]'
    #bash_example10 = '["```bash\\n#!/usr/bin/env bash\\n\\nmanage_gnmi_cert_entry() {\\n    local action=$1\\n    local cname=$2\\n    \\n    nsenter --target 1 --pid --mount --uts --ipc --net bash -c \\"\\n        key=\\"GNMI_CLIENT_CERT|\\\\${TELEMETRY_CLIENT_CNAME}\\"\\n        if [ \\"$action\\" = \\"create\\" ]; then\\n            CURRENT_ENTRY=$(sonic-db-cli CONFIG_DB HGETALL \\"\\\\$key\\")\\n        if [ -z \\"\\\\$CURRENT_ENTRY\\" ]; then\\n                echo \\"Creating \\\\$key entry in CONFIG_DB\\"\\n                RESULT=$(sonic-db-cli CONFIG_DB HSET \\"\\\\$key\\" role \\"gnmi_read\\" 2>&1)\\n                if [ \\\\$? -ne 0 ]; then\\n                    echo \\"Error creating entry: \\\\$RESULT\\" >&2\\n                    exit 1\\n                fi\\n                echo \\"sonic-db-cli HSET result: \\\\$RESULT\\"\\n            else\\n                echo \\"\\\\$key already exists in CONFIG_DB\\"\\n            fi\\n        else\\n            CURRENT_ENTRY=$(sonic-db-cli CONFIG_DB HGETALL \\"\\\\$key\\")\\n            if [ -n \\"\\\\$CURRENT_ENTRY\\" ]; then\\n                echo \\"Removing \\\\$key entry from CONFIG_DB\\"\\n                RESULT=$(sonic-db-cli CONFIG_DB DEL \\"\\\\$key\\" 2>&1)\\n                if [ \\\\$?-ne 0 ]; then\\n                    echo \\"Error removing entry: \\\\$RESULT\\" >&2\\n                    exit 1\\n                fi\\n                echo \\"sonic-db-cli DEL result: \\\\$RESULT\\"\\n            else\\n          echo \\"No \\\\$key entry exists, nothing to remove\\"\\n            fi\\n        fi\\n    \\"\\n}\\n\\n## Populate or remove GNMI client cert entry based on TELEMETRY_CLIENT_CERT_VERIFY_ENABLED\\nif [ -n \\"${TELEMETRY_CLIENT_CNAME}\\" ]; then\\n    if [ \\"${TELEMETRY_CLIENT_CERT_VERIFY_ENABLED}\\" = \\"true\\" ]; then\\n        manage_gnmi_cert_entry \\"create\\" \\"${TELEMETRY_CLIENT_CNAME}\\"\\n    else\\n        manage_gnmi_cert_entry \\"delete\\" \\"${TELEMETRY_CLIENT_CNAME}\\"\\n    fi\\nelse\\n    echo \\"TELEMETRY_CLIENT_CNAME not set, skipping CONFIG_DB update/cleanup\\"\\nfi\\n```"]'
    bash_example10 = '["```bash\\n#!/usr/bin/env bash\\n\\nmanage_gnmi_cert_entry() {\\n    local action=$1\\n    local cname=$2\\n    \\n    nsenter --target 1 --pid --mount --uts --ipc --net bash -c \\"\\n       key=\\\\\\"GNMI_CLIENT_CERT|\\\\${TELEMETRY_CLIENT_CNAME}\\\\\\"\\n          if [ \\\\\\"\\\\$action\\\\\\" = \\\\\\"create\\\\\\" ]; then\\n              CURRENT_ENTRY=\\\\$(sonic-db-cli CONFIG_DB HGETALL \\\\\\"\\\\$key\\\\\\")\\n          if [ -z \\\\\\"\\\\$CURRENT_ENTRY\\\\\\" ]; then\\n                  echo \\\\\\"Creating \\\\$key entry in CONFIG_DB\\\\\\"\\n                  RESULT=\\\\$(sonic-db-cli CONFIG_DB HSET \\\\\\"\\\\$key\\\\\\" role \\\\\\"gnmi_read\\\\\\" 2>&1)\\n                  if [ \\\\$? -ne 0 ]; then\\n                      echo \\\\\\"Error creating entry: \\\\$RESULT\\\\\\" >&2\\n                      exit 1\\n                  fi\\n                  echo \\\\\\"sonic-db-cli HSET result: \\\\$RESULT\\\\\\"\\n              else\\n                  echo \\\\\\"\\\\$key already exists in CONFIG_DB\\\\\\"\\n              fi\\n          else\\n              CURRENT_ENTRY=\\\\$(sonic-db-cli CONFIG_DB HGETALL \\\\\\"\\\\$key\\\\\\")\\n              if [ -n \\\\\\"\\\\$CURRENT_ENTRY\\\\\\" ]; then\\n                  echo \\\\\\"Removing \\\\$key entry from CONFIG_DB\\\\\\"\\n                  RESULT=\\\\$(sonic-db-cli CONFIG_DB DEL \\\\\\"\\\\$key\\\\\\" 2>&1)\\n                  if [ \\\\$? -ne 0 ]; then\\n                      echo \\\\\\"Error removing entry: \\\\$RESULT\\\\\\" >&2\\n                      exit 1\\n                  fi\\n                  echo \\\\\\"sonic-db-cli DEL result: \\\\$RESULT\\\\\\"\\n              else\\n            echo \\\\\\"No \\\\$key entry exists, nothing to remove\\\\\\"\\n              fi\\n          fi\\n      \\"\\n  }\\n  ## Populate or remove GNMI client cert entry based on TELEMETRY_CLIENT_CERT_VERIFY_ENABLED\\n  if [ -n \\"${TELEMETRY_CLIENT_CNAME}\\" ]; then\\n      if [ \\"${TELEMETRY_CLIENT_CERT_VERIFY_ENABLED}\\" = \\"true\\" ]; then\\n          manage_gnmi_cert_entry \\"create\\" \\"${TELEMETRY_CLIENT_CNAME}\\"\\n      else\\n          manage_gnmi_cert_entry \\"delete\\" \\"${TELEMETRY_CLIENT_CNAME}\\"\\n      fi\\n  else\\n      echo \\"TELEMETRY_CLIENT_CNAME not set, skipping CONFIG_DB update/cleanup\\"\\n  fi\\n  ```"]'
    #bash_example10 = '["#!/usr/bin/env bash\\n\\n## Populate or remove GNMI client cert entry based on TELEMETRY_CLIENT_CERT_VERIFY_ENABLED\\nhandle_config_db_entry() {\\n    local action=$1\\n    nsenter --target 1 --pid --mount --uts --ipc --net env TELEMETRY_CLIENT_CNAME=\\"$TELEMETRY_CLIENT_CNAME\\" bash -c \\"\\n  cname=\\\\\\"$TELEMETRY_CLIENT_CNAME\\\\\\"\\n        key=\\\\\\"GNMI_CLIENT_CERT|\\\\\\${cname}\\\\\\"\\n        if [ \\\\\\"$action\\\\\\" = \\\\\\"create\\\\\\" ]; then\\n            CURRENT_ENTRY=$(sonic-db-cli CONFIG_DB HGETALL \\\\\\"$key\\\\\\")\\n            if [ -z \\\\\\"$CURRENT_ENTRY\\\\\\" ]; then\\n                echo \\\\\\"Creating $key entry in CONFIG_DB\\\\\\"\\n                RESULT=$(sonic-db-cli CONFIG_DB HSET \\\\\\"$key\\\\\\" role \\\\\\"gnmi_read\\\\\\")\\n          if [ $? -ne 0 ]; then\\n                    echo \\\\\\"Failed to create $key entry in CONFIG_DB\\\\\\" >&2\\n                exit 1\\n                fi\\n                echo \\\\\\"sonic-db-cli HSET result: $RESULT\\\\\\"\\n     else\\n                echo \\\\\\"$key already exists in CONFIG_DB\\\\\\"\\n            fi\\n        else\\n  CURRENT_ENTRY=$(sonic-db-cli CONFIG_DB HGETALL \\\\\\"$key\\\\\\")\\n            if [ -n \\\\\\"$CURRENT_ENTRY\\\\\\" ]; then\\n                echo \\\\\\"Removing $key entry from CONFIG_DB\\\\\\"\\n                RESULT=$(sonic-db-cli CONFIG_DB DEL \\\\\\"$key\\\\\\")\\n                if [ $? -ne 0 ]; then\\n                    echo \\\\\\"Failed to remove $key entry from CONFIG_DB\\\\\\" >&2\\n                    exit 1\\n                fi\\n                echo \\\\\\"sonic-db-cli DEL result: $RESULT\\\\\\"\\n            else\\n                echo \\\\\\"No $key entry exists, nothing to remove\\\\\\"\\n            fi\\n        fi\\n    \\"\\n}\\n\\nif [ -n \\"${TELEMETRY_CLIENT_CNAME}\\" ]; then\\n    # Optional: Add validation for TELEMETRY_CLIENT_CNAME format\\n    # if ! [[ \\"${TELEMETRY_CLIENT_CNAME}\\" =~ ^[a-zA-Z0-9_]+$ ]]; then\\n    #  echo \\"Invalid TELEMETRY_CLIENT_CNAME format\\" >&2\\n    #     exit 1\\n    # fi\\n    if [ \\"${TELEMETRY_CLIENT_CERT_VERIFY_ENABLED}\\" = \\"true\\" ]; then\\n        handle_config_db_entry \\"create\\"\\n    else\\n        handle_config_db_entry \\"remove\\"\\n    fi\\nelse\\n    if [ \\"${TELEMETRY_CLIENT_CERT_VERIFY_ENABLED}\\" = \\"true\\" ]; then\\n        echo \\"TELEMETRY_CLIENT_CNAME not set, skipping CONFIG_DB update\\"\\n    else\\n        echo \\"TELEMETRY_CLIENT_CNAME not set, skipping CONFIG_DB cleanup\\"\\n    fi\\nfi\\n\\n## Populate serial number to StateDB so telemetry could use it\\n## Only update if decode-syseeprom succeeds and value differs from Redis\\n## Set TELEMETRY_WATCHDOG_SERIALNUMBER_PROBE_ENABLED=true to enable"]'
    comments10 = MockComments(
        code_examples=[bash_example10]
    )

    result10 = format_as_mindmap(comments10)
    print(result10)
    print("\n测试用例10完成")
    
    # 验证测试结果
    # 检查测试用例1是否正确解析了两个代码示例
    example_count1 = result1.count("- 示例 ")
    print(f"\n验证结果:")
    print(f"测试用例1解析出的代码示例数量: {example_count1} (预期: 2)")
    print(f"测试用例1是否正确识别Jinja语法: {'jinja' in result1} (预期: True)")
    
    # 检查测试用例2是否正确处理了单个代码示例
    example_count2 = result2.count("- 示例 ")
    print(f"测试用例2解析出的代码示例数量: {example_count2} (预期: 1)")
    print(f"测试用例2是否正确提取描述: {'这是一个普通的Python示例' in result2} (预期: True)")
    
    # 检查测试用例3是否正确处理了混合类型
    example_count3 = result3.count("- 示例 ")
    print(f"测试用例3解析出的代码示例数量: {example_count3} (预期: 3+)")
    
    # 验证bash语言识别
    bash_count = result6.count("```bash")
    print(f"测试用例6 Bash语言识别数量: {bash_count} (预期: 3)")
    
    # 验证C语言识别
    c_count = result7.count("```c")
    print(f"测试用例7 C语言识别数量: {c_count} (预期: 2)")
    
    # 验证C++语言识别
    cpp_count = result8.count("```cpp")
    print(f"测试用例8 C++语言识别数量: {cpp_count} (预期: 2)")

    bash_count = result9.count("```bash")
    print(f"测试用例9 C++语言识别数量: {bash_count} (预期: 1)")

    bash_count = result10.count("```bash")
    print(f"测试用例10 Bash语言识别数量: {bash_count} (预期: 1)")

if __name__ == "__main__":
    test_format_as_mindmap()