from pathlib import Path
import xml.etree.ElementTree as ET
import collections

COMPONENTS: dict = {
    "Pin": ["Pin"],
    "Logic Gate": ["OR Gate", "AND Gate", "NOT Gate"]
}


def bfs(graph, start) -> set:
    """
    BFS algorithm
    """
    visited = set([start])
    queue = collections.deque([start])

    while queue:
        vertex = queue.popleft()

        for neighbour in graph.get(vertex, []):
            if neighbour not in visited:
                visited.add(neighbour)
                queue.append(neighbour)
    return visited


class Component:
    """Parent class for all components"""
    def __init__(self, name, location, attributes):
        self.name = name
        self.location = location
        self.attributes = attributes

    def get_ports(self):
        return []

    def get_name(self):
        return self.name

    def get_location(self):
        return self.location

    def get_attributes(self):
        return self.attributes


class Pin(Component):
    """
    Special class for Pins

    Input/Output pins with different locations
    """
    def get_ports(self):
        return [{
            "type": "output" if self.attributes.get("output") == "true"
                    else "input",
            "location": self.location
        }]


class LogicGate(Component):
    """
    Special class for Logic Gates such as:

    NOT gate
    OR gate
    AND gate

    TODO: Add more logic gates
    """
    def get_ports(self) -> list[dict]:
        """
        Gets ports from logic gates
        """
        x, y = self.location

        if self.name == "OR Gate":
            return [
                {"type": "input", "location": (x - 50, y - 20)},
                {"type": "input", "location": (x - 50, y + 20)},
                {"type": "output", "location": (x, y)}
            ]
        return []


COMPONENT_CLASSES: dict = {
    "Pin": Pin,
    "Logic Gate": LogicGate
}


class Circuit:
    """
    Special class for Circuits
    """
    def __init__(self, components, wires):
        self.components = components
        self.wires = wires

        self.connections: list = []

        self.components_desc: str = ""
        self.connections_desc: str = ""

    def _numbered_components(self):
        counts = {}
        numbered_components = []

        for component in self.components:
            name = component.get_name()
            counts[name] = counts.get(name, 0) + 1
            numbered_components.append((counts[name], component))

        return numbered_components

    def resolve_connections(self):
        self.connections.clear()
        graph: dict = {}

        for start, end in self.wires:
            graph.setdefault(start, []).append(end)
            graph.setdefault(end, []).append(start)

        already_seen = set()

        numbered_components = self._numbered_components()

        for start in graph:
            if start in already_seen:
                continue

            reachable = bfs(graph, start)
            already_seen.update(reachable)

            connected_ports: list = []
            for component_id, component in numbered_components:
                for port in component.get_ports():
                    location = tuple(port["location"])
                    if location in reachable:
                        connected_ports.append({
                            "id": component_id,
                            "name": component.get_name(),
                            "type": port["type"],
                            "location": location,
                        })
            if connected_ports:
                self.connections.append(connected_ports)

    def describe_components(self) -> str:
        if not self.components:
            return "No components found in the circuit."

        lines = ["\n\nCOMPONENTS IN THE CIRCUIT:\n"]

        for component_id, component in self._numbered_components():
            name = component.get_name()
            label = f"{name} #{component_id}"

            if name == "Pin":
                if component.get_attributes().get("output") == "true":
                    label += " (circuit output)"
                else:
                    label += " (circuit input)"

            lines.append(label)

        return "\n".join(lines)

    def describe_connections(self) -> str:
        if not self.connections:
            return "No connections found in the circuit"

        description_final: str = "\n\nCONNECTIONS IN THE CIRCUIT:\n\n"  # Final description

        for connection in self.connections:
            labels = []

            for port in connection:
                labels.append(
                    f"{port['name']} #{port['id']} {port['type']}"
                )

            description_final += " <-> ".join(labels) + "\n"

        description_final += "-" * 20 + "\n"

        return description_final

    def describe_circuit(self):
        self.resolve_connections()
        components_desc: str = self.describe_components()
        connections_desc: str = self.describe_connections()

        return components_desc + connections_desc

    def get_components(self):
        return self.components

    def get_wires(self):
        return self.wires

    def get_connections(self):
        return self.connections


class CircParser:
    """
    Functional class. Parser of Circuits
    """
    def __init__(self, path):
        self.path: Path = Path(path)

    def parse(self):
        components: list = []
        wires: list = []

        with self.path.open("r", encoding="utf-8") as f:
            lines = f.readlines()
            lines.pop(2)
            root = ET.fromstring("".join(lines))

            circuit = root.find("./circuit[@name='main']")

            if circuit is None:
                raise ValueError("Circuit 'Main' is not found")

            for comp in circuit.findall("comp"):
                name = comp.get("name")
                location = tuple([int(x) for x in \
                            comp.get("loc").replace("(", "").replace(")", "").split(",")])

                if all(name not in COMPONENTS[x] for x in COMPONENTS):
                    raise ValueError(f"No such component: {name}")

                for x in COMPONENTS:
                    if name in COMPONENTS[x]:
                        cls = COMPONENT_CLASSES[x]

                        attributes = dict()
                        for attr in comp.findall("a"):
                            attributes[attr.get("name")] = attr.get("val")

                        component = cls(name, location, attributes)
                        components.append(component)
                        break

            for wire in circuit.findall("wire"):
                fr = [int(x) for x in \
                      wire.get("from").replace("(", "").replace(")", "").split(",")]
                to = [int(x) for x in \
                      wire.get("to").replace("(", "").replace(")", "").split(",")]

                wires.append((tuple(fr), tuple(to)))

        return Circuit(components, wires)


if __name__ == "__main__":
    parser = CircParser("Example.circ")
    circ = parser.parse()

    components = circ.get_components()
    wires = circ.get_wires()
    print(circ.describe_circuit())