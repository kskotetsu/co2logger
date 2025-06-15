"""
データエクスポーター機能のテスト
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
from datetime import datetime, timezone
import json
import io

from co2logger.exporters.base import DataExporterBase
from co2logger.exporters.console import ConsoleExporter
from co2logger.exporters.json_file import JsonFileExporter
from co2logger.exporters.http_sender import HttpSender
from co2logger.models.sensor_data import CO2SensorData


class TestDataExporterBase:
    """データエクスポーター基底クラスのテストケース"""
    
    def test_base_exporter_is_abstract(self):
        """基底クラスが抽象クラスであることをテスト"""
        with pytest.raises(TypeError):
            DataExporterBase()
    
    def test_base_exporter_subclass_must_implement_export(self):
        """サブクラスがexportメソッドを実装する必要があることをテスト"""
        class IncompleteExporter(DataExporterBase):
            pass
        
        with pytest.raises(TypeError):
            IncompleteExporter()


class TestConsoleExporter:
    """コンソールエクスポーターのテストケース"""
    
    @pytest.fixture
    def console_exporter(self):
        """コンソールエクスポーターインスタンスを作成"""
        return ConsoleExporter()
    
    @pytest.fixture
    def sample_co2_data(self):
        """サンプルCO2データを作成"""
        return CO2SensorData(
            timestamp=datetime(2025, 6, 15, 12, 30, 45, tzinfo=timezone.utc),
            co2_ppm=420,
            temperature=25.5,
            humidity=65.0,
            device_address="AA:BB:CC:DD:EE:FF",
            raw_data="test_data"
        )
    
    @pytest.mark.asyncio
    async def test_export_single_data(self, console_exporter, sample_co2_data, capsys):
        """単一データのエクスポートをテスト"""
        await console_exporter.export(sample_co2_data)
        
        captured = capsys.readouterr()
        assert "CO2: 420 ppm" in captured.out
        assert "25.5°C" in captured.out
        assert "65.0%" in captured.out
        assert "AA:BB:CC:DD:EE:FF" in captured.out
    
    @pytest.mark.asyncio
    async def test_export_multiple_data(self, console_exporter, sample_co2_data, capsys):
        """複数データのエクスポートをテスト"""
        data_list = [sample_co2_data, sample_co2_data]
        
        await console_exporter.export(data_list)
        
        captured = capsys.readouterr()
        # 2回出力されることを確認
        assert captured.out.count("CO2: 420 ppm") == 2
    
    def test_format_data_output(self, console_exporter, sample_co2_data):
        """データフォーマット出力をテスト"""
        formatted = console_exporter.format_data(sample_co2_data)
        
        assert "2025-06-15 12:30:45" in formatted
        assert "CO2: 420 ppm" in formatted
        assert "Temp: 25.5°C" in formatted
        assert "Humidity: 65.0%" in formatted
        assert "Device: AA:BB:CC:DD:EE:FF" in formatted
    
    def test_set_verbose_mode(self, console_exporter):
        """詳細モードの設定をテスト"""
        console_exporter.set_verbose(True)
        assert console_exporter.verbose is True
        
        console_exporter.set_verbose(False)
        assert console_exporter.verbose is False
    
    @pytest.mark.asyncio
    async def test_export_with_verbose_mode(self, console_exporter, sample_co2_data, capsys):
        """詳細モードでのエクスポートをテスト"""
        console_exporter.set_verbose(True)
        
        await console_exporter.export(sample_co2_data)
        
        captured = capsys.readouterr()
        # 詳細モードでは生データも出力される
        assert "Raw data: test_data" in captured.out


class TestJsonFileExporter:
    """JSONファイルエクスポーターのテストケース"""
    
    @pytest.fixture
    def json_exporter(self):
        """JSONファイルエクスポーターインスタンスを作成"""
        return JsonFileExporter("/tmp/test_co2_data.json")
    
    @pytest.fixture
    def sample_co2_data(self):
        """サンプルCO2データを作成"""
        return CO2SensorData(
            timestamp=datetime(2025, 6, 15, 12, 30, 45, tzinfo=timezone.utc),
            co2_ppm=420,
            temperature=25.5,
            humidity=65.0,
            device_address="AA:BB:CC:DD:EE:FF"
        )
    
    def test_json_exporter_initialization(self):
        """JSONエクスポーターの初期化をテスト"""
        exporter = JsonFileExporter("/tmp/test.json")
        assert exporter.file_path == "/tmp/test.json"
        assert exporter.append_mode is False
    
    def test_json_exporter_append_mode(self):
        """JSONエクスポーターの追記モードをテスト"""
        exporter = JsonFileExporter("/tmp/test.json", append_mode=True)
        assert exporter.append_mode is True
    
    @pytest.mark.asyncio
    async def test_export_single_data_new_file(self, json_exporter, sample_co2_data):
        """新ファイルへの単一データエクスポートをテスト"""
        mock_file = mock_open()
        
        with patch("builtins.open", mock_file):
            with patch("os.path.exists", return_value=False):
                await json_exporter.export(sample_co2_data)
        
        mock_file.assert_called_once_with("/tmp/test_co2_data.json", "w", encoding="utf-8")
        written_data = "".join(call.args[0] for call in mock_file().write.call_args_list)
        
        # JSON形式で書き込まれたことを確認
        parsed_data = json.loads(written_data)
        assert len(parsed_data) == 1
        assert parsed_data[0]["co2_ppm"] == 420
        assert parsed_data[0]["temperature"] == 25.5
    
    @pytest.mark.asyncio
    async def test_export_append_to_existing_file(self, sample_co2_data):
        """既存ファイルへの追記をテスト"""
        exporter = JsonFileExporter("/tmp/test.json", append_mode=True)
        
        # 既存データをモック
        existing_data = [{"co2_ppm": 400, "temperature": 24.0}]
        mock_file_content = json.dumps(existing_data)
        
        mock_file = mock_open(read_data=mock_file_content)
        
        with patch("builtins.open", mock_file):
            with patch("os.path.exists", return_value=True):
                await exporter.export(sample_co2_data)
        
        # ファイルが読み込まれて書き込まれたことを確認
        assert mock_file().read.called
        
        written_data = "".join(call.args[0] for call in mock_file().write.call_args_list)
        parsed_data = json.loads(written_data)
        
        # 既存データに新データが追加されたことを確認
        assert len(parsed_data) == 2
        assert parsed_data[1]["co2_ppm"] == 420
    
    @pytest.mark.asyncio
    async def test_export_multiple_data(self, json_exporter, sample_co2_data):
        """複数データのエクスポートをテスト"""
        data_list = [sample_co2_data, sample_co2_data]
        mock_file = mock_open()
        
        with patch("builtins.open", mock_file):
            with patch("os.path.exists", return_value=False):
                await json_exporter.export(data_list)
        
        written_data = "".join(call.args[0] for call in mock_file().write.call_args_list)
        parsed_data = json.loads(written_data)
        
        assert len(parsed_data) == 2
    
    @pytest.mark.asyncio
    async def test_export_file_write_error(self, json_exporter, sample_co2_data):
        """ファイル書き込みエラーのテスト"""
        with patch("builtins.open", side_effect=IOError("ファイル書き込みエラー")):
            with pytest.raises(IOError):
                await json_exporter.export(sample_co2_data)


class TestHttpSender:
    """HTTP送信エクスポーターのテストケース"""
    
    @pytest.fixture
    def http_sender(self):
        """HTTP送信エクスポーターインスタンスを作成"""
        return HttpSender("http://localhost:8080/api/sensor-data")
    
    @pytest.fixture
    def sample_co2_data(self):
        """サンプルCO2データを作成"""
        return CO2SensorData(
            timestamp=datetime(2025, 6, 15, 12, 30, 45, tzinfo=timezone.utc),
            co2_ppm=420,
            temperature=25.5,
            humidity=65.0,
            device_address="AA:BB:CC:DD:EE:FF"
        )
    
    def test_http_sender_initialization(self):
        """HTTP送信者の初期化をテスト"""
        sender = HttpSender("http://example.com/api", timeout=30)
        assert sender.url == "http://example.com/api"
        assert sender.timeout == 30
        assert sender.headers["Content-Type"] == "application/json"
    
    def test_set_authentication(self, http_sender):
        """認証設定をテスト"""
        http_sender.set_authentication("Bearer", "test_token")
        assert http_sender.headers["Authorization"] == "Bearer test_token"
    
    def test_add_custom_headers(self, http_sender):
        """カスタムヘッダー追加をテスト"""
        custom_headers = {"X-Device-ID": "sensor_001", "X-API-Version": "v1"}
        http_sender.add_headers(custom_headers)
        
        assert http_sender.headers["X-Device-ID"] == "sensor_001"
        assert http_sender.headers["X-API-Version"] == "v1"
    
    @pytest.mark.asyncio
    async def test_export_single_data_success(self, http_sender, sample_co2_data):
        """単一データの送信成功をテスト"""
        # レスポンスモックをコンテキストマネージャーとして設定
        mock_response = AsyncMock()
        mock_response.__aenter__.return_value.status = 200
        mock_response.__aenter__.return_value.text = AsyncMock(return_value="OK")
        
        with patch("aiohttp.ClientSession.post", return_value=mock_response) as mock_post:
            result = await http_sender.export(sample_co2_data)
            
            assert result is True
            mock_post.assert_called_once()
            
            # 送信されたデータを確認
            call_args = mock_post.call_args
            sent_data = json.loads(call_args.kwargs["data"])
            assert sent_data["co2_ppm"] == 420
    
    @pytest.mark.asyncio
    async def test_export_multiple_data_success(self, http_sender, sample_co2_data):
        """複数データの送信成功をテスト"""
        data_list = [sample_co2_data, sample_co2_data]
        mock_response = AsyncMock()
        mock_response.__aenter__.return_value.status = 200
        
        with patch("aiohttp.ClientSession.post", return_value=mock_response) as mock_post:
            result = await http_sender.export(data_list)
            
            assert result is True
            
            # 送信されたデータを確認
            call_args = mock_post.call_args
            sent_data = json.loads(call_args.kwargs["data"])
            assert len(sent_data) == 2
    
    @pytest.mark.asyncio
    async def test_export_http_error(self, http_sender, sample_co2_data):
        """HTTP送信エラーをテスト"""
        mock_response = AsyncMock()
        mock_response.__aenter__.return_value.status = 500
        mock_response.__aenter__.return_value.text = AsyncMock(return_value="Internal Server Error")
        
        with patch("aiohttp.ClientSession.post", return_value=mock_response):
            result = await http_sender.export(sample_co2_data)
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_export_connection_error(self, http_sender, sample_co2_data):
        """接続エラーをテスト"""
        with patch("aiohttp.ClientSession.post", side_effect=Exception("接続エラー")):
            result = await http_sender.export(sample_co2_data)
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_export_with_retry(self, sample_co2_data):
        """リトライ機能をテスト"""
        sender = HttpSender("http://example.com", max_retries=3)
        
        # 最初の2回は失敗、3回目は成功
        mock_response1 = AsyncMock()
        mock_response1.__aenter__.return_value.status = 500
        mock_response1.__aenter__.return_value.text = AsyncMock(return_value="Error")
        
        mock_response2 = AsyncMock()
        mock_response2.__aenter__.return_value.status = 500
        mock_response2.__aenter__.return_value.text = AsyncMock(return_value="Error")
        
        mock_response3 = AsyncMock()
        mock_response3.__aenter__.return_value.status = 200
        mock_response3.__aenter__.return_value.text = AsyncMock(return_value="OK")
        
        mock_responses = [mock_response1, mock_response2, mock_response3]
        
        with patch("aiohttp.ClientSession.post", side_effect=mock_responses) as mock_post:
            with patch("asyncio.sleep"):  # リトライ待機をスキップ
                result = await sender.export(sample_co2_data)
                
                assert result is True
                assert mock_post.call_count == 3
    
    @pytest.mark.asyncio
    async def test_export_max_retries_exceeded(self, sample_co2_data):
        """最大リトライ数超過をテスト"""
        sender = HttpSender("http://example.com", max_retries=2)
        
        mock_response = AsyncMock()
        mock_response.__aenter__.return_value.status = 500
        mock_response.__aenter__.return_value.text = AsyncMock(return_value="Error")
        
        with patch("aiohttp.ClientSession.post", return_value=mock_response) as mock_post:
            with patch("asyncio.sleep"):
                result = await sender.export(sample_co2_data)
                
                assert result is False
                assert mock_post.call_count == 3  # 初回 + 2回のリトライ