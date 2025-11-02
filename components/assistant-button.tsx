"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { MessageSquare, X, Send } from "lucide-react"
import { Input } from "@/components/ui/input"

export function AssistantButton() {
  const [isOpen, setIsOpen] = useState(false)
  const [messages, setMessages] = useState<Array<{ role: "user" | "assistant"; content: string }>>([])
  const [input, setInput] = useState("")

  const suggestedQuestions = [
    "¿Qué sectores requieren atención hoy?",
    "Dame el top 5 fugas probables",
    "¿Dónde estamos perdiendo más eficiencia energética?",
  ]

  const handleSendMessage = (message: string) => {
    if (!message.trim()) return

    setMessages((prev) => [...prev, { role: "user", content: message }])
    setInput("")

    // Simulate AI response
    setTimeout(() => {
      let response = ""

      if (message.toLowerCase().includes("atención") || message.toLowerCase().includes("requieren")) {
        response =
          "Los sectores que requieren atención prioritaria hoy son:\n\n1. **Sector 233** - Posible fuga con +12% consumo no facturable\n2. **Sector 201** - Fuga confirmada, pérdida energética alta\n3. **Sector 145** - Baja disponibilidad prevista mañana\n\nTe muestro el Sector 233 primero porque su consumo no cobrado subió 12% respecto a su propio histórico, no por comparación con otro sector. Esto no es estacional."
      } else if (message.toLowerCase().includes("fugas")) {
        response =
          "Top 5 sectores con mayor probabilidad de fuga:\n\n1. **Sector 233** (85% probabilidad) - Consumo no facturable +12%\n2. **Sector 201** (92% probabilidad) - Fuga confirmada\n3. **Sector 089** (45% probabilidad) - Variación presión anómala\n4. **Sector 312** (38% probabilidad) - Consumo nocturno elevado\n5. **Sector 078** (25% probabilidad) - Patrón irregular\n\nLa probabilidad se calcula considerando: consumo no facturable, variación de presión, histórico del sector, y reportes de campo."
      } else if (message.toLowerCase().includes("eficiencia") || message.toLowerCase().includes("energética")) {
        response =
          "Sectores con mayor pérdida de eficiencia energética:\n\n1. **Sector 201** - 62% eficiencia (pérdida: 4,200 m³/mes)\n2. **Sector 233** - 68% eficiencia (pérdida: 4,800 m³/mes)\n3. **Sector 078** - 75% eficiencia (pérdida: 2,100 m³/mes)\n\nEstas pérdidas representan alto costo energético en bombeo. Recomiendo priorizar inspección en Sectores 233 y 201."
      } else {
        response =
          "Entiendo tu consulta. Puedo ayudarte con información sobre sectores en riesgo, fugas probables, eficiencia energética, y predicciones de demanda. ¿Sobre qué te gustaría saber más?"
      }

      setMessages((prev) => [...prev, { role: "assistant", content: response }])
    }, 1000)
  }

  return (
    <>
      {/* Floating button */}
      {!isOpen && (
        <Button
          size="lg"
          className="fixed bottom-6 right-6 h-14 w-14 rounded-full shadow-lg"
          onClick={() => setIsOpen(true)}
        >
          <MessageSquare className="h-6 w-6" />
        </Button>
      )}

      {/* Chat panel */}
      {isOpen && (
        <Card className="fixed bottom-6 right-6 w-96 h-[600px] shadow-2xl flex flex-col">
          {/* Header */}
          <div className="p-4 border-b flex items-center justify-between bg-primary text-primary-foreground rounded-t-lg">
            <div>
              <h3 className="font-semibold">Asistente Operativo</h3>
              <p className="text-xs opacity-90">Priorización y análisis</p>
            </div>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setIsOpen(false)}
              className="text-primary-foreground hover:bg-primary-foreground/20"
            >
              <X className="h-5 w-5" />
            </Button>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.length === 0 ? (
              <div className="space-y-4">
                <p className="text-sm text-muted-foreground">
                  Hola, soy tu asistente operativo. Puedo ayudarte a priorizar acciones y analizar el sistema.
                </p>
                <div className="space-y-2">
                  <p className="text-xs font-medium text-muted-foreground">Preguntas sugeridas:</p>
                  {suggestedQuestions.map((question, index) => (
                    <Button
                      key={index}
                      variant="outline"
                      size="sm"
                      className="w-full justify-start text-left h-auto py-2 px-3 bg-transparent"
                      onClick={() => handleSendMessage(question)}
                    >
                      <span className="text-xs leading-relaxed">{question}</span>
                    </Button>
                  ))}
                </div>
              </div>
            ) : (
              messages.map((message, index) => (
                <div key={index} className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}>
                  <div
                    className={`max-w-[80%] rounded-lg p-3 ${
                      message.role === "user" ? "bg-primary text-primary-foreground" : "bg-muted"
                    }`}
                  >
                    <p className="text-sm whitespace-pre-line leading-relaxed">{message.content}</p>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Input */}
          <div className="p-4 border-t">
            <form
              onSubmit={(e) => {
                e.preventDefault()
                handleSendMessage(input)
              }}
              className="flex gap-2"
            >
              <Input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Escribe tu pregunta..."
                className="flex-1"
              />
              <Button type="submit" size="icon">
                <Send className="h-4 w-4" />
              </Button>
            </form>
          </div>
        </Card>
      )}
    </>
  )
}
