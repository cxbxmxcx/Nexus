from barfi import Block


class WorkflowBlock(Block):
    def __init__(self, name="Workflow"):
        super().__init__(name=name)
        self.add_input()
        self.add_output()
        self.add_option(
            name="display-option",
            type="display",
            value="This is a Block with Workflow option.",
        )
        self.add_option(
            name="select-option",
            type="select",
            items=["Select A", "Select B", "Select C"],
            value="Select A",
        )

    def workflow_block_func(self):
        input_1_value = self.get_interface(name="Input 1")
        select_1_value = self.get_option(name="select-option")

        output_1_value = 0
        self.set_interface(name="Output 1", value=output_1_value)

    self.add_compute(workflow_block_func)
