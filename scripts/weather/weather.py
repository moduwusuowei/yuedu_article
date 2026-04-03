# -*- coding: utf-8 -*-
"""
天气查询服务
支持IP定位自动获取城市天气，并提供完善的异常处理
auther: moduwusuowei
"""

import json

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
from typing import Optional, Dict, List
from requests.exceptions import Timeout, ConnectionError, HTTPError
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WeatherService:
    """天气查询服务类"""

    def __init__(self, city: str = "上海", ak: Optional[str] = None):
        """
        初始化天气服务

        Args:
            city: 城市名称
            ak: 百度地图API密钥（可选）
        """
        self.city = city
        self.ak = ak
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

        # 城市代码映射
        self.area_id_map = self._load_area_id_map()
        self.area_id = self.area_id_map.get(city)

        # 文件命名
        self.file_name = f'{city}_weather.txt'

        logger.info(f"天气服务初始化完成，城市: {city}, 区域代码: {self.area_id}")

    def _load_area_id_map(self) -> Dict[str, str]:
        """加载城市代码映射"""
        try:
            with open('area_id.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning("未找到area_id.json文件，将使用默认映射")
            return {
                "北京": "101010100",
                "上海": "101020100",
                "广州": "101280101",
                "深圳": "101280601",
                # 添加更多城市...
            }
        except Exception as e:
            logger.error(f"加载城市代码映射失败: {e}")
            return {}

    def get_weather(self, city_code: Optional[str] = None) -> Optional[Dict]:
        """
        获取天气预报数据

        Args:
            city_code: 城市代码，不传则使用初始化时的城市

        Returns:
            天气数据字典或None
        """
        target_code = city_code or self.area_id

        if not target_code:
            logger.error("未获取到有效的城市代码")
            return None

        url = f'http://www.weather.com.cn/weather/{target_code}.shtml'

        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            response.encoding = 'utf-8'

            soup = BeautifulSoup(response.text, 'lxml')

            # 查找7天天气预报容器
            weather_container = soup.find(id='7d')

            if not weather_container:
                logger.error("未找到天气预报容器")
                return None

            # 解析天气数据
            weather_data = self._parse_weather_data(weather_container)

            return weather_data

        except Timeout:
            logger.error("请求天气数据超时")
            return None
        except ConnectionError:
            logger.error("网络连接失败")
            return None
        except HTTPError as e:
            logger.error(f"HTTP错误: {e}")
            return None
        except Exception as e:
            logger.error(f"获取天气数据时发生未知错误: {e}")
            return None

    def _parse_weather_data(self, container) -> Dict:
        """
        解析天气数据

        Args:
            container: 天气数据容器

        Returns:
            解析后的天气数据
        """
        lines = container.text.split('\n')
        weather_list = []

        # 解析7天天气数据
        for i in range(7):
            try:
                # 日期
                day_index = 6 + i * 17
                day = lines[day_index].strip()

                # 天气状况
                weather_index = day_index + 3
                weather = lines[weather_index].strip()

                # 温度
                temp_index = weather_index + 2
                temperature = lines[temp_index].strip()

                # 风力
                wind_index = temp_index + 7
                wind = lines[wind_index].strip()

                weather_list.append({
                    'date': day,
                    'weather': weather,
                    'temperature': temperature,
                    'wind': wind
                })

            except IndexError:
                logger.warning(f"解析第{i + 1}天天气数据时发生索引错误")
                continue
            except Exception as e:
                logger.warning(f"解析第{i + 1}天天气数据时发生错误: {e}")
                continue

        return {
            'city': self.city,
            'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'weather_list': weather_list
        }

    def save_data(self, weather_data: Dict) -> bool:
        """
        保存天气数据到文件

        Args:
            weather_data: 天气数据字典

        Returns:
            是否保存成功
        """
        if not weather_data:
            logger.error("天气数据为空，无法保存")
            return False

        try:
            with open(self.file_name, 'w', encoding='utf-8') as f:
                # 写入标题
                title = f"{self.city} 天气预报\n查询时间: {weather_data['update_time']}\n\n"
                f.write(title)

                # 写入天气数据
                for item in weather_data['weather_list']:
                    line = f"{item['date']} {item['weather']} {item['temperature']} {item['wind']}\n"
                    f.write(line)

            logger.info(f"天气数据已保存到: {self.file_name}")
            return True

        except Exception as e:
            logger.error(f"保存天气数据失败: {e}")
            return False

    def close(self):
        """关闭会话"""
        self.session.close()
        logger.info("天气服务会话已关闭")


def main():
    """主函数"""
    print("=" * 60)
    print("天气查询服务演示")
    print("=" * 60)

    service = WeatherService()

    try:
        # 1. 查询默认城市天气
        print("\n### 查询默认城市天气 ###")
        weather_data = service.get_weather()

        if weather_data:
            print(f"城市: {weather_data['city']}")
            print(f"更新时间: {weather_data['update_time']}")
            print("\n未来7天天气预报:")

            for i, item in enumerate(weather_data['weather_list'], 1):
                print(f"{i}. {item['date']} {item['weather']} {item['temperature']} {item['wind']}")

            # 保存数据
            service.save_data(weather_data)

        # 2. 查询指定城市天气
        print("\n### 查询指定城市天气 ###")
        cities = ["北京", "上海", "广州"]

        for city in cities:
            service.city = city
            service.area_id = service.area_id_map.get(city)

            if service.area_id:
                print(f"\n查询{city}天气...")
                weather_data = service.get_weather()

                if weather_data:
                    print(f"{city}今日天气: {weather_data['weather_list'][0]['weather']}")
                    print(f"温度: {weather_data['weather_list'][0]['temperature']}")

                time.sleep(1)  # 避免请求过快

    finally:
        service.close()
        print("\n" + "=" * 60)
        print("演示结束")
        print("=" * 60)


if __name__ == '__main__':
    main()
