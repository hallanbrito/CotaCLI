import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami
import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.plasmoid
import org.kde.plasma.plasma5support as Plasma5Support

PlasmoidItem {
    id: root
    property var providers: []
    property string failure: ""
    property bool busy: false
    readonly property color backgroundColor: "#14151d"
    readonly property color foregroundColor: "#f0f0f5"
    readonly property color mutedColor: "#a5a8b9"
    readonly property color accentColor: "#937aff"

    toolTipMainText: "CotaCLI"
    toolTipSubText: busy ? "Atualizando cotas…" : (failure || compactText())
    Plasmoid.contextualActions: [
        PlasmaCore.Action {
            text: "Atualizar cotas"
            icon.name: "view-refresh"
            enabled: !root.busy
            onTriggered: root.refresh(true)
        }
    ]

    function percent(window) {
        if (!window || typeof window.remaining !== "number") return "--"
        return window.remaining.toFixed(0) + "%"
    }

    function resetAt(window) {
        if (!window || typeof window.reset !== "number" || window.reset <= 0) return ""
        return "Reseta " + Qt.formatDateTime(new Date(window.reset * 1000), "dd/MM HH:mm")
    }

    function compactText() {
        if (busy && providers.length === 0) return "Cotas…"
        if (providers.length === 0) return "CotaCLI"
        var summary = []
        for (var i = 0; i < providers.length; i++) {
            var item = providers[i]
            var label = item.id === "codex" ? "Cx" :
                item.id === "agy-gemini" ? "Gm" :
                item.id === "agy-others" ? "A+" : "Cl"
            summary.push(label + " " + percent(item.windows && item.windows["5h"]))
        }
        return summary.join(" · ")
    }

    function refresh(force) {
        if (busy) return
        busy = true
        failure = ""
        var command = "/bin/sh -c 'PATH=\"$HOME/.local/bin:$PATH\"; export PATH; exec \"$HOME/.local/bin/cotacli\" snapshot"
            + (force ? " --refresh" : "") + "'"
        executable.connectSource(command)
        watchdog.restart()
    }

    Plasma5Support.DataSource {
        id: executable
        engine: "executable"
        onNewData: function(sourceName, data) {
            disconnectSource(sourceName)
            watchdog.stop()
            root.busy = false
            if (data["exit code"] !== undefined && data["exit code"] !== 0) {
                root.failure = "Não foi possível executar CotaCLI. Reinstale pelo pacote."
                return
            }
            try {
                var payload = JSON.parse(String(data.stdout || ""))
                if (payload.schema !== 1 || !(payload.providers instanceof Array))
                    throw new Error("Contrato inválido")
                root.providers = payload.providers
            } catch (error) {
                root.failure = "O CotaCLI não retornou dados válidos."
            }
        }
    }

    Timer {
        id: watchdog
        interval: 75000
        repeat: false
        onTriggered: {
            executable.connectedSources = []
            root.busy = false
            root.failure = "A consulta demorou demais; tente atualizar novamente."
        }
    }

    Timer {
        interval: 600000
        running: true
        repeat: true
        onTriggered: root.refresh(false)
    }

    Component.onCompleted: refresh(false)

    compactRepresentation: Item {
        Layout.minimumWidth: 24
        Layout.preferredWidth: 28
        Layout.preferredHeight: 28
        Kirigami.Icon {
            anchors.centerIn: parent
            width: 22
            height: 22
            source: "view-statistics"
        }
        MouseArea {
            property bool wasExpanded: false
            anchors.fill: parent
            onPressed: wasExpanded = root.expanded
            onClicked: root.expanded = !wasExpanded
        }
    }

    fullRepresentation: Rectangle {
        Layout.preferredWidth: 442
        Layout.preferredHeight: Math.min(610, Math.max(190, 45 + root.providers.length * 126))
        color: "#11131b"
        radius: 14

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 12
            spacing: 8

            QQC2.Label {
                visible: root.failure.length > 0
                text: root.failure
                color: "#ff9a9a"
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }

            QQC2.Label {
                visible: !root.busy && root.providers.length === 0 && !root.failure
                text: "Nenhuma CLI compatível detectada."
                color: root.mutedColor
            }

            QQC2.ScrollView {
                id: scroll
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                ColumnLayout {
                    width: scroll.width - 10
                    spacing: 10
                    Repeater {
                        model: root.providers
                        delegate: Rectangle {
                            id: card
                            required property var modelData
                            Layout.fillWidth: true
                            readonly property string statusText: String(modelData.status || "")
                            readonly property bool hasWarning: statusText.length > 0
                                && statusText.indexOf("automático") !== 0
                            Layout.preferredHeight: hasWarning ? 128 : 110
                            radius: 10
                            color: "#1a1c27"
                            border.color: "#303243"

                            ColumnLayout {
                                anchors.fill: parent
                                anchors.margins: 12
                                spacing: 9
                                QQC2.Label {
                                    text: card.modelData.name
                                    color: root.foregroundColor
                                    font.bold: true
                                    font.pixelSize: 14
                                }
                                RowLayout {
                                    Layout.fillWidth: true
                                    spacing: 14
                                    Repeater {
                                        model: [
                                            {name: "5 HORAS", value: card.modelData.windows && card.modelData.windows["5h"]},
                                            {name: "SEMANAL", value: card.modelData.windows && card.modelData.windows.week}
                                        ]
                                        delegate: ColumnLayout {
                                            id: metric
                                            required property var modelData
                                            Layout.fillWidth: true
                                            Layout.preferredWidth: 1
                                            spacing: 6
                                            RowLayout {
                                                Layout.fillWidth: true
                                                QQC2.Label {
                                                    text: metric.modelData.name
                                                    color: root.mutedColor
                                                    font.pixelSize: 11
                                                    Layout.fillWidth: true
                                                }
                                                QQC2.Label {
                                                    text: root.percent(metric.modelData.value)
                                                    color: root.foregroundColor
                                                    font.bold: true
                                                    font.pixelSize: 13
                                                }
                                            }
                                            Rectangle {
                                                Layout.fillWidth: true
                                                Layout.preferredHeight: 4
                                                radius: 2
                                                color: "#3b3d4e"
                                                Rectangle {
                                                    width: parent.width * Math.max(0, Math.min(100,
                                                        (metric.modelData.value && metric.modelData.value.remaining) || 0)) / 100
                                                    height: parent.height
                                                    radius: parent.radius
                                                    color: root.accentColor
                                                }
                                            }
                                            QQC2.Label {
                                                text: root.resetAt(metric.modelData.value)
                                                color: root.mutedColor
                                                font.pixelSize: 10
                                                elide: Text.ElideRight
                                                Layout.fillWidth: true
                                            }
                                        }
                                    }
                                }
                                QQC2.Label {
                                    visible: card.hasWarning
                                    text: card.statusText
                                    color: "#ffbc7d"
                                    elide: Text.ElideRight
                                    Layout.fillWidth: true
                                    font.pixelSize: 10
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
