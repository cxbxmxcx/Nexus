import yaml
from lark import Lark, Token, Transformer, Tree, v_args

from nexus.nexus_base.context_variables import tracking_function_context
from nexus.nexus_base.nexus_models import ThoughtTemplate, db


def append_tracking_context(function):
    tf = tracking_function_context.get("Not set")
    tracking_function_context.set(f"{tf}:{function}")


def remove_tracking_context(function):
    tf = tracking_function_context.get("Not set")
    tracking_function_context.set(f"{tf.replace(f':{function}', '')}")


class TemplateTransformer(Transformer):
    def __init__(self, parser, context, agent, helpers=None, manager=None):
        self.parser = parser
        self.context = context
        self.agent = agent
        self.manager = manager
        self.helpers = helpers

    @v_args(inline=True)
    def variable(self, items):
        if isinstance(items, list):
            name = items[0].value
        elif isinstance(items, str):
            name = items
        value = self.context.get(name, "")
        #     print(f"Variable '{name}': {value}")
        return value

    def VAR(self, items):
        if isinstance(items, list):
            name = items[0].value
        elif isinstance(items, str):
            name = items
        return name

    @v_args(inline=True)
    def partial(self, *items):
        name = items[0].value
        args = items[1:]
        # Process arguments for partials
        processed_args = [self.transform(arg) for arg in args]

        # Convert all elements to strings
        args_str = "".join(self.convert_to_string(arg) for arg in processed_args)
        if "," in args_str:
            args_str = args_str.split(",")
        elif " " in args_str:
            args_str = args_str.split(" ")
        else:
            args_str = [args_str]

        args = {}
        for arg in args_str:
            if isinstance(arg, str):
                earg = self.context.get(arg, "")
                if earg:
                    args[arg] = earg

        partial_template = self.manager.get_thought_template(name)

        if partial_template:
            append_tracking_context(f"partial:{name}")
            partial_result = self.manager.execute_template(
                self.agent,
                partial_template.content,
                self.context,
                None,
                partial_execution=True,
            )
            remove_tracking_context(f"partial:{name}")
        return partial_result

    @v_args(inline=True)
    def helper(self, *items):
        name = items[0].value
        if name not in self.helpers:
            print(f"Helper '{name}' not found")
            return ""

        args = items[1:]
        # Process arguments for helpers
        processed_args = [self.transform(arg) for arg in args]

        # Convert all elements to strings
        args_str = "".join(self.convert_to_string(arg) for arg in processed_args)
        if "," in args_str:
            args_str = args_str.split(",")
        elif " " in args_str:
            args_str = args_str.split(" ")
        else:
            args_str = [args_str]

        args = []
        for arg in args_str:
            if isinstance(arg, str):
                earg = self.context.get(arg, "")
                if earg:
                    args.append(earg)

        helper_func = self.helpers[name]
        result = helper_func(*args)
        print(f"Helper '{name}' with args: {args}, result: {result}")
        return result

    @v_args(inline=True)
    def start_lone_brace(self, *items):
        return "{"

    @v_args(inline=True)
    def end_lone_brace(self, *items):
        return "}"

    @v_args(inline=True)
    def lone_double_brace(self, *items):
        return "}}"

    @v_args(inline=True)
    def text(self, items):
        text_value = "".join(items)
        # print(f"Text: {text_value}")
        return text_value

    @v_args(inline=True)
    def template(self, *items):
        if isinstance(items, str):
            return items
        if isinstance(items, list) or isinstance(items, tuple):
            return "".join(items)
        result = "".join(self.transform(self.parser.parse(c)) for c in items)
        print(f"Template result: {result}")
        return result

    def convert_to_string(self, item):
        if isinstance(item, Tree):
            return "".join(self.convert_to_string(child) for child in item.children)
        elif isinstance(item, Token):
            return str(item)
        else:
            return str(item)


class ThoughtTemplateManager:
    def __init__(self, nexus):
        self.nexus = nexus
        self.parser = self.init_template_parser()

    def init_template_parser(self):
        template_grammar = """        
        ?start: template

        template: (text | variable | partial | helper )*

        text: /[^\\{\\}]+/

        variable: "{{" VAR "}}"
        partial: "{{>" VAR partial_args "<}}"
        partial_args: (variable | text)*
        helper: "{{#" VAR helper_args "#}}"
        helper_args: (variable | text)*        

        %import common.CNAME -> VAR
        %import common.WS_INLINE
        %ignore WS_INLINE
        """
        template_grammar = """        
            ?start: template

            template: (text | variable | partial | helper | start_lone_brace | end_lone_brace | lone_double_brace)*

            text: /[^\\{\\}]+/
            start_lone_brace: "{" 
            end_lone_brace: "}"  // Rule to handle single braces
            lone_double_brace: "}}" // Rule to handle lone closing double braces

            variable: "{{" VAR "}}"
            partial: "{{>" VAR partial_args "}}"
            partial_args: (variable | text)*
            helper: "{{#" VAR helper_args "}}"
            helper_args: (variable | text)*        

            %import common.CNAME -> VAR
           
        """
        return Lark(
            template_grammar,
            start="start",
            parser="lalr",
        )

    def add_thought_template(self, template_name, template_content):
        with db.atomic():
            if (
                ThoughtTemplate.select()
                .where(ThoughtTemplate.name == template_name)
                .exists()
            ):
                raise ValueError("Template name already exists")
            ThoughtTemplate.create(
                name=template_name,
                content=template_content,
            )
            print(f"Thought template '{template_name}' added.")
            return True

    def get_thought_template(self, template_name):
        try:
            return ThoughtTemplate.get(ThoughtTemplate.name == template_name)
        except ThoughtTemplate.DoesNotExist:
            return None

    def update_thought_template(self, template_name, template_content):
        with db.atomic():
            template = ThoughtTemplate.get(ThoughtTemplate.name == template_name)
            template.content = template_content
            template.save()
            print(f"Thought template '{template_name}' updated.")
            return True

    def delete_thought_template(self, template_name):
        with db.atomic():
            query = ThoughtTemplate.delete().where(
                ThoughtTemplate.name == template_name
            )
            return query.execute()

    def get_thought_template_names(self):
        return [template.name for template in ThoughtTemplate.select()]

    def _extract_set_variables(self, template_data, invars):
        variables = {}
        for key, value in template_data.items():
            if key == "template" or key == "type":
                continue
            if isinstance(value, str):
                variables[key] = value
            elif isinstance(value, dict):
                variables[key] = invars.get(key, value.get("default", ""))
        return variables

    def load_template_data(self, content):
        template_data = None
        try:
            template_data = yaml.safe_load(content)
        except yaml.YAMLError as e:
            if hasattr(e, "problem_mark"):
                mark = e.problem_mark
                error_message = (
                    f"Error at line {mark.line + 1}, column {mark.column + 1}: {str(e)}"
                )
            else:
                error_message = str(e)
            raise ValueError(
                f"Error loading YAML content: {error_message}\n\n{content}"
            )
        return template_data

    def get_thought_template_inputs_outputs(self, template_content):
        template_data = self.load_template_data(template_content)

        tinputs = template_data.get("inputs", {})
        toutputs = template_data.get("outputs", {})

        tinputs = {
            key: value
            for key, value in tinputs.items()
            if isinstance(value, dict) and "type" in value
        }
        toutputs = {
            key: value
            for key, value in toutputs.items()
            if isinstance(value, dict) and "type" in value
        }
        return tinputs, toutputs

    def execute_template(
        self, agent, content, inputs, outputs, partial_execution=False
    ):
        nexus = self.nexus

        template_data = self.load_template_data(content)

        # ttype = template_data.get("type", "prompt")  # prompt, function/action, semantic
        tinputs = template_data.get("inputs", {})
        toutputs = template_data.get("outputs", {})
        thelpers = template_data.get("helpers", {})

        einputs = self._extract_set_variables(tinputs, inputs)

        helpers = {}
        for name, code in thelpers.items():
            exec(code, locals())  # load the helper functions into the locals namespace
            helpers[name] = locals()[
                f"{name}"
            ]  # add the helper function to the helpers dictionary

        input_prompt = tinputs.get("template", "")
        outputs = {}
        iprompt = None
        oprompt = None
        iresult = None
        oresult = None

        if input_prompt:
            parsed_tree = self.parser.parse(input_prompt)

            # Transform the parsed tree
            transformer = TemplateTransformer(
                self.parser,
                einputs,
                agent,
                helpers=helpers,
                manager=self,
            )
            iprompt = transformer.transform(parsed_tree)

            if tinputs.get("type") == "prompt":
                append_tracking_context("input_prompt")
                output = agent.get_semantic_response(agent.profile.persona, iprompt)
                remove_tracking_context("input_prompt")
                outputs["output"] = output
            elif tinputs.get("type") == "function":
                outputs["output"] = iprompt
            else:
                outputs["output"] = iprompt
            iresult = outputs["output"]

        eoutputs = (
            inputs | outputs
        )  # self._extract_set_variables(toutputs, outputs | inputs)
        output_prompt = toutputs.get("template", "")
        if output_prompt and eoutputs:
            parsed_tree = self.parser.parse(output_prompt)

            # Transform the parsed tree
            transformer = TemplateTransformer(
                self.parser,
                eoutputs,
                agent,
                helpers=helpers,
                manager=self,
            )
            oprompt = transformer.transform(parsed_tree)

            if toutputs.get("type") == "prompt":
                append_tracking_context("output_prompt")
                oresult = agent.get_semantic_response(agent.profile.persona, oprompt)
                append_tracking_context("output_prompt")
            elif toutputs.get("type") == "function":
                oresult = oprompt
            else:
                oresult = oprompt

        if partial_execution:
            if oresult is None:
                return iresult
            else:
                return oresult
        return iprompt, iresult, oprompt, oresult
