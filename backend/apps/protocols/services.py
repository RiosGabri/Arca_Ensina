import ast
import operator
from decimal import Decimal

from django.utils import timezone

from .engine.interpreter import GuidedProtocolInterpreter
from .models import ProtocolExecutionState


class ProtocolExecutionEngine:
    def primeiro_step(self, version):
        return version.steps.order_by("order").first()

    def comecar(self, execution, context=None):
        if execution.version.steps_data.get("steps"):
            interpreter = GuidedProtocolInterpreter(execution.version.steps_data)
            execution.current_step_key = interpreter.get_first_step_id()
            execution.current_step = None
            execution.save(update_fields=["current_step_key", "current_step"])

            entry_warnings = interpreter.evaluate_entry_gates(context or {})
            step_warnings = interpreter.evaluate_step_gates(
                execution.current_step_key, context or {}
            )
            all_warnings = entry_warnings + step_warnings

            ProtocolExecutionState.objects.create(
                execution=execution,
                step_key=execution.current_step_key,
                values=context or {},
                gate_warnings=all_warnings,
            )
            return execution

        primeiro_step = self.primeiro_step(execution.version)
        execution.current_step = primeiro_step
        execution.save(update_fields=["current_step"])

        ProtocolExecutionState.objects.create(
            execution=execution,
            step=primeiro_step,
            values=context or {},
        )
        return execution

    def resposta_step_atual(self, execution, valores):
        if execution.current_step_key:
            return self._resposta_step_json(execution, valores)

        step = execution.current_step

        if step.step_type == step.StepType.CALCULO_DERIVADO:
            formula = step.config.get("formula")
            output_field = step.config.get("output_field", "result")
            
            if formula:
                valores = {
                    **valores,
                    output_field: self.calcular_formula(
                        formula,
                        self.montar_contexto(execution, valores),
                        ),
                }

        state, created = ProtocolExecutionState.objects.update_or_create(
            execution=execution,
            step=step,
            defaults={"values": valores},
        )

        next_step = self.escolher_prox_step(step, valores, state)

        if next_step is None:
            execution.current_step = None
            execution.status = execution.Status.CONCLUIDO
            execution.finished_at = timezone.now()
            execution.save(update_fields=["current_step", "status", "finished_at"])
        else:
            execution.current_step = next_step
            execution.save(update_fields=["current_step"])

        return state

    def escolher_prox_step(self, step, valores, state=None):
        if step.step_type == step.StepType.SIM_NAO:
            resposta = valores.get("answer")

            if resposta is True:
                next_id = step.config.get("true_next_step_id")
            else:
                next_id = step.config.get("false_next_step_id")

            if next_id:
                return step.version.steps.filter(id=next_id).first()

        if step.step_type == step.StepType.CHECKLIST:
            checked_items = valores.get("checked_items", [])
            min_checked = step.config.get("min_checked", 1)

            if len(checked_items) >= min_checked:
                next_id = step.config.get("true_next_step_id")
            else:
                next_id = step.config.get("false_next_step_id")

            if next_id:
                return step.version.steps.filter(id=next_id).first()

        if step.step_type == step.StepType.LOOP_TITULACAO:
            iteracoes = step.config.get("max_iterations", 1)
            loops = (state.loop_count if state else 0) + 1

            if state:
                state.loop_count = loops
                state.save(update_fields=["loop_count"])

            if loops >= iteracoes:
                next_id = step.config.get("max_reached_next_step_id")
            else:
                next_id = step.config.get("loop_next_step_id")

            if next_id:
                return step.version.steps.filter(id=next_id).first()
            
        if step.step_type== step.StepType.MULTIPLA_ESCOLHA:
            escolha = valores.get("choice")
            choices_next_step_ids = step.config.get("choices_next_step_ids", {})
            next_id = choices_next_step_ids.get(escolha)

            if next_id:
                return step.version.steps.filter(id=next_id).first()


        return step.next_step

    def calcular_formula(self, formula, contexto):
        #agora VAI
        operadores={
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Pow: operator.pow,
            ast.USub: operator.neg,
        }
    
        def avaliar(node):
            if isinstance(node, ast.Constant):
                if isinstance(node.value, (int, float)):
                    return Decimal(str(node.value))
                raise ValueError("A fórmulaa só aceita números!")

            if isinstance(node, ast.Name):
                if node.id not in contexto:
                    raise ValueError(f"Variável Desconhecida: {node.id}")
                return Decimal(str(contexto[node.id]))
            
            if isinstance(node, ast.BinOp):
                operador = operadores.get(type(node.op))
                if operador is None:
                    raise ValueError("Operador inválido")
                
                esquerda = avaliar(node.left)
                direita = avaliar(node.right)
                return operador(esquerda, direita)
            
            if isinstance(node, ast.UnaryOp):
                operador = operadores.get(type(node.op))
                if operador is None:
                    raise ValueError("Operador Inválido")

                valor = avaliar(node.operand)
                return operador(valor)    
            
            raise ValueError(
                "Expressão Inválida: Use apenas números,"
                " variáveis e operações."
            )
            
    
        tree = ast.parse(formula, mode="eval")
        result = avaliar(tree.body)
        if isinstance(result, Decimal):
            return float(result)
        return result
    
    def montar_contexto(self, execution, valores_atuais=None):
        contexto={}

        for state in execution.states.select_related("step").order_by("answered_at"):
            contexto.update(state.values)

        if valores_atuais:
            contexto.update(valores_atuais)
        
        return contexto

    def _resposta_step_json(self, execution, valores):
        interpreter = GuidedProtocolInterpreter(execution.version.steps_data)
        step_key = execution.current_step_key
        step = interpreter.get_step(step_key)

        # Conecta com valores existentes para manter contexto
        existing_values = {}
        try:
            existing = ProtocolExecutionState.objects.get(
                execution=execution, step_key=step_key
            )
            existing_values = existing.values
        except ProtocolExecutionState.DoesNotExist:
            pass
        merged_values = {**existing_values, **valores}

        if step and step.get("type") == "derived_calc":
            history = self._historico_json(execution)
            context = interpreter.build_context(history, merged_values)
            merged_values = interpreter.apply_derived_calculation(
                step_key, merged_values, context
            )

        # Avalia os gates do step antes de responder
        history = self._historico_json(execution)
        context = interpreter.build_context(history, merged_values)
        current_warnings = interpreter.evaluate_step_gates(step_key, context)

        state, created = ProtocolExecutionState.objects.update_or_create(
            execution=execution,
            step_key=step_key,
            defaults={"values": merged_values, "gate_warnings": current_warnings},
        )

        next_step_key = interpreter.resolve_next_step_id(
            step_key,
            valores,
            {"loop_count": state.loop_count},
        )

        if step and step.get("type") == "titration_loop":
            state.loop_count += 1
            state.save(update_fields=["loop_count"])

        if next_step_key is None:
            execution.current_step_key = None
            execution.current_step = None
            execution.status = execution.Status.CONCLUIDO
            execution.finished_at = timezone.now()
            execution.save(
                update_fields=[
                    "current_step_key",
                    "current_step",
                    "status",
                    "finished_at",
                ]
            )
        else:
            execution.current_step_key = next_step_key
            execution.current_step = None
            execution.save(update_fields=["current_step_key", "current_step"])

        return state

    def _historico_json(self, execution):
        return [
            {
                "step_key": state.step_key,
                "values": state.values,
            }
            for state in execution.states.filter(step_key__isnull=False).order_by(
                "answered_at"
            )
        ]

    def avancar_step(self, execution):
        if not execution.current_step_key:
            raise ValueError("Avanço sem resposta só suportado em modo JSON.")

        interpreter = GuidedProtocolInterpreter(execution.version.steps_data)
        current_step = interpreter.get_step(execution.current_step_key)

        if not current_step:
            raise ValueError("Step atual não encontrado.")

        next_step_key = current_step.get("next_step")

        if next_step_key is None:
            execution.current_step_key = None
            execution.current_step = None
            execution.status = execution.Status.CONCLUIDO
            execution.finished_at = timezone.now()
            execution.save(
                update_fields=[
                    "current_step_key",
                    "current_step",
                    "status",
                    "finished_at",
                ]
            )
        else:
            execution.current_step_key = next_step_key
            execution.current_step = None
            execution.save(update_fields=["current_step_key", "current_step"])

        return execution

    def get_reminders(self, execution):
        """Retorna lembretes de steps wait_reassess com due_at e status."""
        reminders = []
        if not execution.version.steps_data:
            return reminders

        interpreter = GuidedProtocolInterpreter(execution.version.steps_data)
        now = timezone.now()

        for state in execution.states.filter(step_key__isnull=False):
            step = interpreter.get_step(state.step_key)
            if step and step.get("type") == "wait_reassess":
                duration = step.get("duration_hours", 0)
                due_at = (
                    state.answered_at + timezone.timedelta(hours=duration)
                    if duration
                    else None
                )

                status = "info"
                if due_at:
                    if now > due_at:
                        status = "overdue"
                    else:
                        status = "pending"

                reminders.append({
                    "step_id": state.step_key,
                    "step_title": step.get("title", ""),
                    "answered_at": state.answered_at.isoformat(),
                    "due_at": due_at.isoformat() if due_at else None,
                    "status": status,
                    "duration_hours": duration,
                    "reassess_fields": step.get("reassess_fields", []),
                    "phases": step.get("phases", []),
                })

        return reminders
