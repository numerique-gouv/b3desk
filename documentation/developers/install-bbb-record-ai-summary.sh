#!/bin/bash -ex

AI_PROVIDER="${1:-${AI_PROVIDER:-}}"
AI_API_KEY="${2:-${AI_API_KEY:-}}"

usage() {
  echo "Usage: $0 <ai-provider> <api-key>"
  echo ""
  echo "Supported ai-provider values: claude, openai, albert"
  echo "You can also set AI_PROVIDER and AI_API_KEY in the environment."
}

if [[ -z "$AI_PROVIDER" || -z "$AI_API_KEY" ]]; then
  usage
  exit 1
fi

case "$AI_PROVIDER" in
  claude)
    LLM_API_KEY_PATH=".llm.anthropic_api_key"
    TRANSCRIPTION_PROVIDER=""
    ;;
  openai)
    LLM_API_KEY_PATH=".llm.openai_api_key"
    TRANSCRIPTION_PROVIDER="openai"
    ;;
  albert)
    LLM_API_KEY_PATH=".llm.albert_api_key"
    TRANSCRIPTION_PROVIDER="albert"
    ;;
  *)
    echo "Unsupported ai-provider: $AI_PROVIDER"
    usage
    exit 1
    ;;
esac

sudo apt update

# LIVEKIT
sudo apt-get install bbb-livekit -y || true
sudo yq e -i '.livekit.enabled = true' /etc/bigbluebutton/bbb-webrtc-sfu/production.yml
sudo systemctl restart bbb-webrtc-sfu
sudo systemctl restart livekit-server
echo "audioBridge=livekit" | sudo tee -a /etc/bigbluebutton/bbb-web.properties
sudo systemctl restart bbb-web nginx

# DEB
sudo apt install debhelper po-debconf -y || true

wget -O /tmp/bbb-record-ai-summary-ai-summary-new-format.zip https://bigbluebutton.nyc3.digitaloceanspaces.com/bbb-record-ai-summary-ai-summary-new-format.zip
cd /tmp
unzip -o bbb-record-ai-summary-ai-summary-new-format.zip
cd /tmp/bbb-record-ai-summary-ai-summary-new-format/
sudo ./build.sh

cd ..
sudo apt install ./bbb-record-ai-summary_0.1.0_all.deb -y || true

sudo touch /etc/bigbluebutton/ai-summary.yml
sudo yq eval ".llm.provider = \"$AI_PROVIDER\"" -i /etc/bigbluebutton/ai-summary.yml
sudo yq eval "$LLM_API_KEY_PATH = \"$AI_API_KEY\"" -i /etc/bigbluebutton/ai-summary.yml
sudo yq eval '.llm.language = "en"' -i /etc/bigbluebutton/ai-summary.yml

sudo touch /etc/bigbluebutton/post-archive-transcription.yml
sudo yq eval '.language = "en"' -i /etc/bigbluebutton/post-archive-transcription.yml
if [[ -n "$TRANSCRIPTION_PROVIDER" ]]; then
  sudo yq eval ".${TRANSCRIPTION_PROVIDER}.api_key = \"$AI_API_KEY\"" -i /etc/bigbluebutton/post-archive-transcription.yml
else
  echo "Skipping transcription API key setup for provider '$AI_PROVIDER' because no matching transcription backend is available."
fi


captions_type="$(yq eval '.steps.captions | tag' /usr/local/bigbluebutton/core/scripts/bigbluebutton.yml 2>/dev/null || true)"

# normalize steps.captions to an array.
if [[ "$captions_type" == "!!str" ]]; then
  captions_value="$(yq eval '.steps.captions' /usr/local/bigbluebutton/core/scripts/bigbluebutton.yml)"
  if [[ -n "$captions_value" && "$captions_value" != "null" ]]; then
    sudo CAPTIONS_VALUE="$captions_value" \
      yq eval -i '.steps.captions = [strenv(CAPTIONS_VALUE)]' /usr/local/bigbluebutton/core/scripts/bigbluebutton.yml
  fi
fi

# check for the new config entry and add it only if missing.
captions_type="$(yq eval '.steps.captions | tag' /usr/local/bigbluebutton/core/scripts/bigbluebutton.yml 2>/dev/null || true)"
if [[ "$captions_type" == "!!seq" ]]; then
  has_ai_summary="$(yq eval '.steps.captions[] | select(. == "process:ai-summary")' /usr/local/bigbluebutton/core/scripts/bigbluebutton.yml 2>/dev/null || true)"
  if [[ -z "$has_ai_summary" ]]; then
    sudo yq eval -i '.steps.captions = .steps.captions + ["process:ai-summary"]' /usr/local/bigbluebutton/core/scripts/bigbluebutton.yml
  fi
  sudo yq eval -i '.steps.captions[] style="double"' /usr/local/bigbluebutton/core/scripts/bigbluebutton.yml
fi



sudo yq eval '.steps."process:ai-summary" = "publish:ai-summary"' -i /usr/local/bigbluebutton/core/scripts/bigbluebutton.yml
sudo yq eval -i '.steps."process:ai-summary" style="double"' /usr/local/bigbluebutton/core/scripts/bigbluebutton.yml

sudo yq eval -i '
    .steps."process:ai-summary" = "publish:ai-summary" |
    (.steps."process:ai-summary" | key) style="double" |
    .steps."process:ai-summary" style="double"
  ' /usr/local/bigbluebutton/core/scripts/bigbluebutton.yml


sudo systemctl restart bbb-rap-resque-worker livekit-server bbb-webrtc-recorder


bbb-conf --salt
