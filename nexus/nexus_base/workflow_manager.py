import json
from collections import defaultdict


class WorkflowNode:
    def __init__(self, name, node_type=None, options=None, inputs=None, outputs=None):
        self.name = name
        self.node_type = node_type
        self.options = options if options is not None else {}
        self.inputs = inputs if inputs is not None else {}
        self.outputs = outputs if outputs is not None else {}

    def execute(self, **kwargs):
        # Adjust to process inputs as needed for the function
        print(f"Executing {self.name} with args {kwargs}")

        if self.node_type == "User Input":
            output = kwargs
        elif self.node_type == "Memory Augmentation":
            output = {"Augmented Input": kwargs["Input"]}
        elif self.node_type == "Knowledge Augmentation":
            output = {"Augmented Input": kwargs["Input"]}
        elif self.node_type == "Reasoning Augmentation":
            output = {"Reasoning": kwargs["Plans"]}
        elif self.node_type == "Call LLM":
            output = {"Response": "Response"}
        elif self.node_type == "Actions":
            output = {"Actions": "Actions"}
        elif self.node_type == "Plans":
            output = {"Plans": "Plans"}
        elif self.node_type == "Extract Memories":
            output = {"Memories": "Memories"}
        elif self.node_type == "Persist to Memory":
            output = {}
        elif self.node_type == "Extract Actions":
            output = {"Actions": "Actions"}
        elif self.node_type == "Execute Plans":
            output = {"Plan Results": "Plan Results"}
        elif self.node_type == "Execute Actions":
            output = {"Action Results": "Action Results"}
        elif self.node_type == "Extract Plans":
            output = {"Plans": "Plans"}
        elif self.node_type == "Call LLM Results":
            output = {"Response": "Response", "Evaluations": "Evaluations"}
        elif self.node_type == "Provide Feedback":
            output = {"Feedback": "Feedback"}
        else:
            output = {}

        print(f"----------------------- Output of {self.name}: {output}")
        return output

        # if kwargs:
        #     return kwargs
        # else:
        #     outputs = {}
        #     for key, value in self.outputs.items():
        #         outputs[key] = value["value"]
        #     return outputs


class WorkflowManager:
    def __init__(self):
        self.graph = defaultdict(list)
        self.nodes = {}

    def add_node(
        self, node_name, node_type=None, options=None, inputs=None, outputs=None
    ):
        self.nodes[node_name] = WorkflowNode(
            node_name,
            node_type=node_type,
            options=options,
            inputs=inputs,
            outputs=outputs,
        )

    def add_edge(
        self, from_node, to_node, from_output_key="default", to_input_key=None
    ):
        # Define edges with output and input keys for targeted data routing
        if from_node in self.nodes and to_node in self.nodes:
            self.graph[from_node].append((to_node, from_output_key, to_input_key))
        else:
            raise ValueError(
                f"One or both nodes '{from_node}', '{to_node}' do not exist."
            )

    def execute_workflow(self, **kwargs):
        # Assuming a topological sort is available and no cycles exist,
        # this executes nodes in order, routing outputs to inputs as defined.
        order = self.topological_sort()
        outputs = {}
        inputs = {}

        for idx, node_name in enumerate(order):
            if idx == 0:
                inputs[node_name] = kwargs
            node = self.nodes[node_name]
            if inputs.get(node_name) is not None:
                outputs[node_name] = node.execute(
                    **inputs[node_name]
                )  # returns a dictionary of outputs
            else:
                outputs[node_name] = node.execute()

            for out_node, out_key, in_key in self.graph[node_name]:
                if inputs.get(out_node) is None:
                    inputs[out_node] = {}
                for key, value in outputs[node_name].items():
                    if key == in_key:
                        inputs[out_node][key] = value

    def is_cyclic_util(self, node, visited, rec_stack):
        visited[node] = True
        rec_stack[node] = True
        for neighbour in self.graph[node]:
            if not visited[neighbour]:
                if self.is_cyclic_util(neighbour, visited, rec_stack):
                    return True
            elif rec_stack[neighbour]:
                return True
        rec_stack[node] = False
        return False

    def is_cyclic(self):
        visited = {node: False for node in self.nodes}
        rec_stack = {node: False for node in self.nodes}
        for node in self.nodes:
            if not visited[node]:
                if self.is_cyclic_util(node, visited, rec_stack):
                    return True
        return False

    def topological_sort(self):
        # Dictionary to keep track of each node's degree of incoming edges
        in_degree = {node: 0 for node in self.nodes}
        for node in self.nodes:
            for adj in self.graph[node]:
                in_degree[adj[0]] += 1

        # Use a queue to keep track of nodes with no incoming edge
        queue = [node for node in self.nodes if in_degree[node] == 0]
        top_order = []

        while queue:
            node = queue.pop(0)
            top_order.append(node)

            # Decrease in-degree by 1 for all its neighboring nodes
            for adj in self.graph[node]:
                in_degree[adj[0]] -= 1
                # If in-degree becomes zero, add it to queue
                if in_degree[adj[0]] == 0:
                    queue.append(adj[0])

        # Check if there was a cycle
        if len(top_order) != len(self.nodes):
            raise Exception(
                "There exists a cycle in the graph, cannot perform topological sort."
            )

        return top_order

    def import_from_json(self, json_str):
        import_dict = json.loads(json_str)
        for node_name, node_info in import_dict.items():
            options = node_info["block"].get("options", {})
            inputs = node_info["block"]["inputs"]
            outputs = node_info["block"]["outputs"]
            node_type = node_info["block"]["type"]
            self.add_node(
                node_name,
                node_type=node_type,
                options=options,
                inputs=inputs,
                outputs=outputs,
            )

        for node_name, node_info in import_dict.items():
            for interface_name, interface in node_info["interfaces"].items():
                if interface and interface["type"] == "output":
                    for to_node, to_interface in interface["to"].items():
                        self.add_edge(
                            from_node=node_name,
                            to_node=to_node,
                            from_output_key=interface_name,
                            to_input_key=to_interface,
                        )


# Example usage:
workflow = """
 {"User Input-1": {"block": {"name": "User Input-1", "type": "User Input", "inputs": {}, "outputs": {"Input": {"value": null, "id": "ni_17120014177331"}, "History": {"value": null, "id": "ni_17120014177332"}}, "interface_names": ["Input", "History"], "options": {}}, "type": "User Input", "interfaces": {"Input": {"type": "output", "to": {"Memory Augmentation-1": "Input", "Knowledge Augmentation-1": "Input", "Call LLM-1": "Input", "Reasoning Augmentation-1": "Input"}}, "History": {"type": "output", "to": {"Call LLM-1": "History"}}}}, "Memory Augmentation-1": {"block": {"name": "Memory Augmentation-1", "type": "Memory Augmentation", "inputs": {"Input": {"value": null, "id": "ni_171200143374911"}}, "outputs": {"Augmented Input": {"value": null, "id": "ni_171200143374912"}}, "interface_names": ["Input", "Augmented Input"], "options": {}}, "type": "Memory Augmentation", "interfaces": {"Input": {"type": "intput", "from": {"User Input-1": "Input"}}, "Augmented Input": {"type": "output", "to": {"Call LLM-1": "Memory Augmentation"}}}}, "Knowledge Augmentation-1": {"block": {"name": "Knowledge Augmentation-1", "type": "Knowledge Augmentation", "inputs": {"Input": {"value": null, "id": "ni_171200144201818"}}, "outputs": {"Augmented Input": {"value": null, "id": "ni_171200144201819"}}, "interface_names": ["Input", "Augmented Input"], "options": {}}, "type": "Knowledge Augmentation", "interfaces": {"Input": {"type": "intput", "from": {"User Input-1": "Input"}}, "Augmented Input": {"type": "output", "to": {"Call LLM-1": "Knowledge Augmentation"}}}}, "Reasoning Augmentation-1": {"block": {"name": "Reasoning Augmentation-1", "type": "Reasoning Augmentation", "inputs": {"Input": {"value": null, "id": "ni_171201747269610"}, "Plans": {"value": null, "id": "ni_171200200774210"}}, "outputs": {"Reasoning": {"value": null, "id": "ni_171200200774211"}}, "interface_names": ["Input", "Plans", "Reasoning"], "options": {}}, "type": "Reasoning Augmentation", "interfaces": {"Input": {"type": "intput", "from": {"User Input-1": "Input"}}, "Plans": {"type": "intput", "from": {"Plans-1": "Plans"}}, "Reasoning": {"type": "output", "to": {"Call LLM-1": "Reasoning"}}}}, "Call LLM-1": {"block": {"name": "Call LLM-1", "type": "Call LLM", "inputs": {"Input": {"value": null, "id": "ni_171200148926737"}, "History": {"value": null, "id": "ni_171200148926738"}, "Actions": {"value": null, "id": "ni_171200200774215"}, "Plans": {"value": null, "id": "ni_171200200774216"}, "Memory Augmentation": {"value": null, "id": "ni_171200200774317"}, "Knowledge Augmentation": {"value": null, "id": "ni_171200200774318"}, "Reasoning": {"value": null, "id": "ni_171200200774319"}}, "outputs": {"Response": {"value": null, "id": "ni_171200148926740"}}, "interface_names": ["Input", "History", "Actions", "Plans", "Memory Augmentation", "Knowledge Augmentation", "Reasoning", "Response"], "options": {}}, "type": "Call LLM", "interfaces": {"Input": {"type": "intput", "from": {"User Input-1": "Input"}}, "History": {"type": "intput", "from": {"User Input-1": "History"}}, "Actions": {"type": "intput", "from": {"Actions-1": "Actions"}}, "Plans": {"type": "intput", "from": {"Plans-1": "Plans"}}, "Memory Augmentation": {"type": "intput", "from": {"Memory Augmentation-1": "Augmented Input"}}, "Knowledge Augmentation": {"type": "intput", "from": {"Knowledge Augmentation-1": "Augmented Input"}}, "Reasoning": {"type": "intput", "from": {"Reasoning Augmentation-1": "Reasoning"}}, "Response": {"type": "output", "to": {"Extract Memories-1": "Response", "Extract Actions-1": "Response", "Extract Plans-1": "Response", "Provide Feedback-1": "Response"}}}}, "Actions-1": {"block": {"name": "Actions-1", "type": "Actions", "inputs": {}, "outputs": {"Actions": {"value": null, "id": "ni_171200202838530"}}, "interface_names": ["Actions"], "options": {}}, "type": "Actions", "interfaces": {"Actions": {"type": "output", "to": {"Call LLM-1": "Actions"}}}}, "Plans-1": {"block": {"name": "Plans-1", "type": "Plans", "inputs": {}, "outputs": {"Plans": {"value": null, "id": "ni_171200204958038"}}, "interface_names": ["Plans"], "options": {}}, "type": "Plans", "interfaces": {"Plans": {"type": "output", "to": {"Call LLM-1": "Plans", "Reasoning Augmentation-1": "Plans"}}}}, "Extract Memories-1": {"block": {"name": "Extract Memories-1", "type": "Extract Memories", "inputs": {"Response": {"value": null, "id": "ni_171200211666157"}}, "outputs": {"Memories": {"value": null, "id": "ni_171200211666158"}}, "interface_names": ["Response", "Memories"], "options": {}}, "type": "Extract Memories", "interfaces": {"Response": {"type": "intput", "from": {"Call LLM-1": "Response"}}, "Memories": {"type": "output", "to": {"Persist to Memory-1": "Memories"}}}}, "Persist to Memory-1": {"block": {"name": "Persist to Memory-1", "type": "Persist to Memory", "inputs": {"Memories": {"value": null, "id": "ni_171200213941563"}}, "outputs": {}, "interface_names": ["Memories"], "options": {}}, "type": "Persist to Memory", "interfaces": {"Memories": {"type": "intput", "from": {"Extract Memories-1": "Memories"}}}}, "Extract Actions-1": {"block": {"name": "Extract Actions-1", "type": "Extract Actions", "inputs": {"Response": {"value": null, "id": "ni_171200224672155"}}, "outputs": {"Actions": {"value": null, "id": "ni_171200224672156"}}, "interface_names": ["Response", "Actions"], "options": {}}, "type": "Extract Actions", "interfaces": {"Response": {"type": "intput", "from": {"Call LLM-1": "Response"}}, "Actions": {"type": "output", "to": {"Execute Actions-1": "Actions"}}}}, "Execute Plans-1": {"block": {"name": "Execute Plans-1", "type": "Execute Plans", "inputs": {"Plans": {"value": null, "id": "ni_171200227455963"}}, "outputs": {"Plan Results": {"value": null, "id": "ni_171200227455964"}}, "interface_names": ["Plans", "Plan Results"], "options": {}}, "type": "Execute Plans", "interfaces": {"Plans": {"type": "intput", "from": {"Extract Plans-1": "Plans"}}, "Plan Results": {"type": "output", "to": {"Call LLM Results-1": "Plan Results"}}}}, "Execute Actions-1": {"block": {"name": "Execute Actions-1", "type": "Execute Actions", "inputs": {"Actions": {"value": null, "id": "ni_171200229227866"}}, "outputs": {"Action Results": {"value": null, "id": "ni_171200229227867"}}, "interface_names": ["Actions", "Action Results"], "options": {}}, "type": "Execute Actions", "interfaces": {"Actions": {"type": "intput", "from": {"Extract Actions-1": "Actions"}}, "Action Results": {"type": "output", "to": {"Call LLM Results-1": "Action Results"}}}}, "Extract Plans-1": {"block": {"name": "Extract Plans-1", "type": "Extract Plans", "inputs": {"Response": {"value": null, "id": "ni_171200231546873"}}, "outputs": {"Plans": {"value": null, "id": "ni_171200231546874"}}, "interface_names": ["Response", "Plans"], "options": {}}, "type": "Extract Plans", "interfaces": {"Response": {"type": "intput", "from": {"Call LLM-1": "Response"}}, "Plans": {"type": "output", "to": {"Execute Plans-1": "Plans"}}}}, "Call LLM Results-1": {"block": {"name": "Call LLM Results-1", "type": "Call LLM Results", "inputs": {"Action Results": {"value": null, "id": "ni_171200236577683"}, "Plan Results": {"value": null, "id": "ni_171200236577684"}, "Feedback": {"value": null, "id": "ni_171200236577685"}}, "outputs": {"Response": {"value": null, "id": "ni_171200236577686"}, "Evaluations": {"value": null, "id": "ni_171200236577687"}}, "interface_names": ["Action Results", "Plan Results", "Feedback", "Response", "Evaluations"], "options": {}}, "type": "Call LLM Results", "interfaces": {"Action Results": {"type": "intput", "from": {"Execute Actions-1": "Action Results"}}, "Plan Results": {"type": "intput", "from": {"Execute Plans-1": "Plan Results"}}, "Feedback": {"type": "intput", "from": {"Provide Feedback-1": "Feedback"}}, "Response": {}, "Evaluations": {}}}, "Provide Feedback-1": {"block": {"name": "Provide Feedback-1", "type": "Provide Feedback", "inputs": {"Response": {"value": null, "id": "ni_171200239597897"}}, "outputs": {"Feedback": {"value": null, "id": "ni_171200239597898"}}, "interface_names": ["Response", "Feedback"], "options": {}}, "type": "Provide Feedback", "interfaces": {"Response": {"type": "intput", "from": {"Call LLM-1": "Response"}}, "Feedback": {"type": "output", "to": {"Call LLM Results-1": "Feedback"}}}}}
 """
wm = WorkflowManager()
wm.import_from_json(workflow)

wm.execute_workflow(Input="Test", History=["Test1", "Test2"])
