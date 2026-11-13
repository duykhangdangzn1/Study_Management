"""Du lieu hoc phan nganh Tin hoc Xay dung (trich tu TomTat_hocPhan.docx)."""

PROGRAM = {'code': '7580201',
 'elective_required': 2,
 'faculty': 'KHOA XÂY DỰNG',
 'major': 'KỸ THUẬT XÂY DỰNG',
 'name': 'TIN HỌC XÂY DỰNG',
 'name_en': 'CONSTRUCTION INFORMATICS',
 'semesters': 9,
 'total_credits': 156}

COURSES = [{'id': 1,
  'semester': 1,
  'name': 'Giải tích',
  'credits': 4.0,
  'elective': False,
  'prereq': [],
  'coreq': [],
  'prereq_text': '',
  'coreq_text': '',
  'hours': {'lt': '4', 'da': '', 'pbl': '', 'th': '', 'tt': ''},
  'desc': 'Học phần Giải tích cung cấp các kiến thức cơ bản về lý thuyết tập hợp, về giới hạn, sự liên tục, phép tính '
          'vi phân, phép tính tích phân và bài toán cực trị của hàm số một biến và hàm số nhiều biến. Học phần cũng đề '
          'cập tới một số ứng dụng của phép tính vi phân, tích phân ; ứng dụng của một số phần mềm hỗ trợ tính toán , '
          'đồ họa và có một số ví dụ thiết lập mô hình toán cho các bài toán liên quan tới công nghệ và kĩ thuật .'},
 {'id': 2,
  'semester': 1,
  'name': 'Vật lý Cơ và Nhiệt',
  'credits': 3.0,
  'elective': False,
  'prereq': [],
  'coreq': [],
  'prereq_text': '',
  'coreq_text': '',
  'hours': {'lt': '3', 'da': '', 'pbl': '', 'th': '', 'tt': ''},
  'desc': 'Học phần Vật lý Cơ – Nhiệt cung cấp cho người học những kiến thức trong Vật lý ở phần Cơ học và Nhiệt động '
          'lực học, bao gồm: - Các tính chất, các qui luật chuyển động của chất điểm , vật rắn và chất lưu ; - Mối '
          'liên hệ giữa các đại lượng đặc trưng của chuyển động, các định lý, định luật liên quan đến động lượng, '
          'momen động lượng, năng lượng; - Các định luật chất khí , phương trình trạng thái của khí lý tưởng ; - Mối '
          'liên hệ giữa công, nhiệt và nội năng trong các quá trình biến đổi nhiệt động và ứng dụng để khảo sát hoạt '
          'động của các lại máy nhiệt .'},
 {'id': 3,
  'semester': 1,
  'name': 'Thí nghiệm Vật lý (cơ và nhiệt)',
  'credits': 1.0,
  'elective': False,
  'prereq': [],
  'coreq': [2],
  'prereq_text': '',
  'coreq_text': 'Vật lý Cơ và Nhiệt',
  'hours': {'lt': '', 'da': '', 'pbl': '', 'th': '1', 'tt': ''},
  'desc': 'Học phần này bao gồm 0 5 bài thí nghiệm thuộc học phần Điện Từ học và Quang học: Bài 1: Làm quen với các '
          'dụng cụ đo cơ bản Bài 2: Xác định hệ số ma sát trượt sử dụng mặt phẳng nghiêng Bài 3: Đo momen quán tính '
          'của vật rắn sử dụng phương pháp dao động Bài 4: Đo hệ số nhớt của chất lỏng sử dụng phương pháp Stokes Bài '
          '5: Đo hệ số nở dài của vật rắn'},
 {'id': 4,
  'semester': 1,
  'name': 'Nhập môn ngành',
  'credits': 2.0,
  'elective': False,
  'prereq': [],
  'coreq': [],
  'prereq_text': '',
  'coreq_text': '',
  'hours': {'lt': '2', 'da': '', 'pbl': '', 'th': '', 'tt': ''},
  'desc': 'Học phần Nhập môn ngành được tổ chức đào tạo ở học kỳ thứ nhất. Học phần này cung cấp cho sinh viên tổng '
          'quan về nghề nghiệp và cấu trúc chương trình đào tạo ngành Kỹ thuật xây dựng chuyên ngành Tin học xây dựng; '
          'giúp sinh viên bước đầu hình thành những kỹ năng cá nhân, kỹ năng giao tiếp; giúp sinh viên làm quen các '
          'trải nghiệm tư duy thiết kế dự án kỹ thuật để chuẩn bị cho việc học tập trong các học kỳ sa u .'},
 {'id': 5,
  'semester': 1,
  'name': 'Triết học Mác - Lênin',
  'credits': 3.0,
  'elective': False,
  'prereq': [],
  'coreq': [],
  'prereq_text': '',
  'coreq_text': '',
  'hours': {'lt': '3', 'da': '', 'pbl': '', 'th': '', 'tt': ''},
  'desc': 'Học phần Triết học Mác – Lênin, cung cấp cho người học những kiến thức cơ bản về triết học Mác- Lênin, giúp '
          'cho người học những hiểu được những nội dung cơ bản về chủ nghĩa duy vật biện chứng, phép biện chứng duy '
          'vật, chủ nghĩa duy vật lịch sử.'},
 {'id': 6,
  'semester': 1,
  'name': 'Hình họa - Vẽ kỹ thuật',
  'credits': 3.0,
  'elective': False,
  'prereq': [],
  'coreq': [],
  'prereq_text': '',
  'coreq_text': '',
  'hours': {'lt': '2.5', 'da': '', 'pbl': '', 'th': '0.5', 'tt': ''},
  'desc': 'Học phần Hình họa – Vẽ kỹ thuật trang bị cho sinh viên ngôn ngữ đồ họa kỹ thuật cơ bản dùng trong giao tiếp '
          'và biểu diễn các đối tượng kỹ thuật trong lĩnh vực xây dựng. Nội dung học phần tập trung vào Các phương '
          'pháp biểu diễn đối tượng không gian lên mặt phẳng thông qua hệ thống hình chiếu vuông góc và hình chiếu '
          'trục đo; hệ thống tiêu chuẩn bản vẽ kỹ thuật xây dựng (TCVN & ISO); kỹ thuật xây dựng hình chiếu thứ ba và '
          'các hình biểu diễn chuyên sâu (hình cắt, mặt cắt, hình chiếu phụ và hình chiếu riêng phần). Thực hành: Sử '
          'dụng phần mềm AutoCAD để thiết lập bản vẽ kỹ thuật điện tử chuẩn xác , tạo tiền đề cho việc ứng dụng các '
          'công cụ kỹ thuật số tiên tiến (BIM/Revit) vào thực tiễn ngành xây dựng.'},
 {'id': 7,
  'semester': 1,
  'name': 'Nhập môn công nghệ số và ứng dụng trí tuệ nhân tạo',
  'credits': 2.0,
  'elective': False,
  'prereq': [],
  'coreq': [],
  'prereq_text': '',
  'coreq_text': '',
  'hours': {'lt': '2', 'da': '', 'pbl': '', 'th': '', 'tt': ''},
  'desc': 'Học phần này nhằm cung cấp cho sinh viên các kiến thức nền tảng về công nghệ số và trí tuệ nhân tạo (AI); '
          'các kỹ năng sử dụng một số công cụ số và AI cơ bản trong học tập, nghiên cứu và cuộc sống; đồng thời hình '
          'thành nhận thức về vai trò và tác động của công nghệ số và AI trong kỷ nguyên số .'},
 {'id': 8,
  'semester': 2,
  'name': 'Chủ nghĩa xã hội khoa học',
  'credits': 2.0,
  'elective': False,
  'prereq': [5],
  'coreq': [],
  'prereq_text': 'Triết học Mác - Lênin',
  'coreq_text': '',
  'hours': {'lt': '2', 'da': '', 'pbl': '', 'th': '', 'tt': ''},
  'desc': 'Học phần được kết cấu thành 2 phần chính: - Một là, nghiên cứu những vấn đề cốt lõi nhất về Chủ nghĩa xã '
          'hội khoa học, một trong ba bộ phận cấu thành chủ nghĩa Mác - Lênin. - Hai là, nghiên cứu những vấn đề chính '
          'trị - xã hội của Việt Nam liên quan đến chủ nghĩa xã hội và con đường đi lên chủ nghĩa xã hội ở Việt Nam.'},
 {'id': 9,
  'semester': 2,
  'name': 'Giải tích nâng cao',
  'credits': 4.0,
  'elective': False,
  'prereq': [1],
  'coreq': [],
  'prereq_text': 'Giải tích',
  'coreq_text': '',
  'hours': {'lt': '4', 'da': '', 'pbl': '', 'th': '', 'tt': ''},
  'desc': 'Học phần c ung cấp cho sinh viên các kiến thức về giải tích vector ( Tích phân bội, tích phân đường và tích '
          'phân mặt ), lý thuyết chuỗi và phương trình vi phân cùng với các ứng dụng trong các lĩnh vực khoa học kỹ '
          'thuật. Học ph ầ n cũng giới thiệu một số ứng dụng của một số phần mềm hỗ trợ tính toán, đồ họa và có một số '
          'ví dụ thiết lập mô hình toán cho các bài toán liên quan tới công nghệ và kĩ thuật'},
 {'id': 10,
  'semester': 2,
  'name': 'Đại số tuyến tính',
  'credits': 3.0,
  'elective': False,
  'prereq': [],
  'coreq': [],
  'prereq_text': '',
  'coreq_text': '',
  'hours': {'lt': '3', 'da': '', 'pbl': '', 'th': '', 'tt': ''},
  'desc': 'Học phần trang bị những kiến thức cơ sở về đại số tuyến tính bao gồm: Tập hợp, ánh xạ và s ố phức; Ma trận '
          'và đ ịnh thức; Hệ phương trình tuyến tính; Không gian vectơ và á nh xạ tuyến tính ; Dạng toàn phương. Đây '
          'là những công cụ toán học nền tảng giúp sinh viên giải quyết các bài toán kỹ thuật, mô hình hóa dữ liệu và '
          'phát triển tư duy thuật toán trong các môn chuyên ngành. Thông qua học phần, sinh viên không chỉ nắm vững '
          'kỹ thuật tính toán mà còn hình thành khả năng phân tích logic, chuẩn bị cho việc tiếp nhận các kiến thức '
          'công nghệ và kỹ thuật phức tạp hơn.'},
 {'id': 11,
  'semester': 2,
  'name': 'Anh văn A2.2',
  'credits': 4.0,
  'elective': False,
  'prereq': [],
  'coreq': [],
  'prereq_text': '',
  'coreq_text': '',
  'hours': {'lt': '4', 'da': '', 'pbl': '', 'th': '', 'tt': ''},
  'desc': 'Học phần này được thiết kế tích hợp giữa 4 kỹ năng: Nghe, Nói, Đọc, Viết và các bài tập Ngữ pháp, Từ vựng, '
          'Luyện âm. Nội dung học phần được trình bày trong 6 bài học (6 units), mỗi unit gồm các bài học về các kỹ '
          'năng sử dụng từ vựng; kĩ năng nghe hiểu (nghe hiểu được các câu và cấu trúc được sử dụng thường xuyên liên '
          'quan đến nhu cầu giao tiếp cơ bản với các dạng bài tập trắc nghiệm, hoàn thành câu/ sơ đồ/ bảng biểu); kĩ '
          'năng đọc hiểu (đọc hiểu được các câu và cấu trúc được sử dụng thường xuyên liên quan đến nhu cầu giao tiếp '
          'cơ bản với dạng bài tập trắc nghiệm, nối thông tin, trả lời ngắn); kỹ năng nói (trao đổi thông tin về những '
          'chủ đề đơn giản, quen thuộc hằng ngày, mô tả đơn giản về bản thân, môi trường xung quanh và những vấn đề '
          'thuộc nhu cầu thiết yếu); kĩ năng viết (với các dạng bài tập ngữ pháp và viết (hoàn thành câu, viết câu, '
          'viết đoạn văn ngắn về gia đình, điều kiện sống, ghi chú, email, một tin nhắn cảm ơn, biết cách viết một '
          'blog cá nhân về du lịch, tin nhắn qua mạng, bình luận về một số chủ đề: học tập, giải trí, ngoại hình, thời '
          'trang…) Sau mỗi bài học, sinh viên được luyện tập, thực hành với các tài liệu cho hình thức học trực tiếp '
          'và nguồn tài nguyên thực hành trực tuyến.'},
 {'id': 12,
  'semester': 2,
  'name': 'Ngôn ngữ lập trình trong xây dựng',
  'credits': 2.0,
  'elective': False,
  'prereq': [],
  'coreq': [],
  'prereq_text': '',
  'coreq_text': '',
  'hours': {'lt': '2', 'da': '', 'pbl': '', 'th': '', 'tt': ''},
  'desc': 'Học phần Ngôn ngữ lập trình trong xây dựng là học phần thuộc khối kiến thức cơ sở ngành tin học xây dựng, '
          'cung cấp cho sinh viên các khái niệm cơ bản và nâng cao trong ngôn ngữ lập trình C# (C-sharp) như biến, '
          'loại dữ liệu, toán tử, câu điều kiện và vòng lặp, phương thức , mảng và các kỹ thuật xử lý nâng cao. Học '
          'phần còn giới thiệu cách tổ chức chương trình thành các hàm, giới thiệu kỹ thuật lập trình hướng đối tượng '
          'OOP (object-oriented programming) để giải quyết các bài toán trong xây dựng'},
 {'id': 13,
  'semester': 2,
  'name': 'Hóa đại cương',
  'credits': 2.0,
  'elective': False,
  'prereq': [],
  'coreq': [],
  'prereq_text': '',
  'coreq_text': '',
  'hours': {'lt': '2', 'da': '', 'pbl': '', 'th': '', 'tt': ''},
  'desc': 'Học phần trang bị hệ thống kiến thức nền tảng về hóa học đại cương, đi từ các định luật cơ bản đến cấu tạo '
          'chi tiết của nguyên tử, phân tử và quy luật biến thiên tính chất trong bảng tuần hoàn các nguyên tố. Sinh '
          'viên được nghiên cứu chuyên sâu về bản chất liên kết hóa học, kết hợp với các nguyên lý nhiệt động học, '
          'động học và cân bằng hóa học để giải thích chiều hướng cũng như tốc độ của các quá trình biến đổi chất. Bên '
          'cạnh đó, các nội dung về hệ dung dịch và điện hóa học cũng được chú trọng nhằm xây dựng cơ sở lý thuyết '
          'vững chắc cho người học. Thông qua việc tích hợp giữa lý thuyết và các nội dung thực nghiệm, học phần giúp '
          'sinh viên hình thành tư duy phân tích khoa học, làm chủ kỹ năng tính toán định lượng và tạo tiền đề quan '
          'trọng cho việc tiếp cận các môn học chuyên ngành tiếp theo.'},
 {'id': 14,
  'semester': 2,
  'name': 'Cơ lý thuyết',
  'credits': 2.0,
  'elective': False,
  'prereq': [2],
  'coreq': [],
  'prereq_text': 'Vật lý Cơ và Nhiệt',
  'coreq_text': '',
  'hours': {'lt': '2', 'da': '', 'pbl': '', 'th': '', 'tt': ''},
  'desc': 'Học phần Cơ lý thuyết trang bị cho sinh viên các kiến thức nền tảng về cơ học vật rắn tuyệt đối, bao gồm ba '
          'nội dung cốt lõi: Tĩnh học, Động học và Động lực học. Sinh viên được rèn luyện khả năng mô hình hóa các bài '
          'toán cơ học, xác định lực và phản lực liên kết, phân tích điều kiện cân bằng của vật rắn và hệ vật rắn, xác '
          'định các đặc trưng động học của điểm và vật rắn, đồng thời vận dụng các định luật và định lý cơ bản của '
          'động lực học để thiết lập và giải các bài toán chuyển động. Học phần là nền tảng quan trọng cho việc học '
          'tập các học phần cơ sở và chuyên ngành của khối ngành xây dựng như Sức bền vật liệu, Cơ học kết cấu, Kết '
          'cấu công trình, Cơ học đất, Kỹ thuật thi công, đồng thời góp phần hình thành tư duy phân tích và năng lực '
          'giải quyết các vấn đề kỹ thuật trong thực tiễn xây dựng.'},
 {'id': 15,
  'semester': 3,
  'name': 'Lịch sử Đảng Cộng sản Việt Nam',
  'credits': 2.0,
  'elective': False,
  'prereq': [5],
  'coreq': [],
  'prereq_text': 'Triết học Mác - Lênin',
  'coreq_text': '',
  'hours': {'lt': '2', 'da': '', 'pbl': '', 'th': '', 'tt': ''},
  'desc': 'Học phần Lịch sử Đảng Cộng sản Việt Nam mô tả các sự kiện lịch sử Đảng giúp sinh viên hiểu rõ nội dung, '
          'tính chất, bản chất của các sự kiện đó gắn liền với sự lãnh đạo của Đảng. Các sự kiện đó thể hiện quá trình '
          'Đảng ra đời, phát triển và lãnh đạo sự nghiệp giải phóng dân tộc, kháng chiến cứu quốc và xây dựng, phát '
          'triển đất nước theo con đường XHCN, trên các lĩnh vực chính trị, quân sự, kinh tế, xã hội, văn hóa, quốc '
          'phòng, an ninh, đối ngoại .'},
 {'id': 16,
  'semester': 3,
  'name': 'Cấu trúc và cơ sở dữ liệu trong xây dựng',
  'credits': 2.0,
  'elective': False,
  'prereq': [7],
  'coreq': [],
  'prereq_text': 'Nhập môn công nghệ số và ứng dụng trí tuệ nhân tạo',
  'coreq_text': '',
  'hours': {'lt': '2', 'da': '', 'pbl': '', 'th': '', 'tt': ''},
  'desc': 'Học phần nhằm cung cấp cho sinh viên các kiến thức cơ bản về cấu trúc dữ liệu; cơ sở dữ liệu quan hệ, các '
          'phép toán đại số quan hệ, chuẩn hóa cơ sở dữ liệu và ngôn ngữ truy vấn cơ sở dữ liệu. Sau khi kết thúc học '
          'phần, sinh viên có thể vận dụng được cấu trúc dữ liệu cơ bản như danh sách liên kết, ngăn xếp, hàng đợi, '
          'cây và đồ thị để giải quyết các bài toán lập trình bằng cách sử dụng các thuật toán tìm kiếm, sắp xếp dữ '
          'liệu. Sử dụng hệ quản trị SQLServer làm công cụ để cài đặt, thao tác, truy vấn dữ liệu và lập trình cơ sở '
          'dữ liệu. Làm tiền đề cho các môn học phân tích, thiết kế và cài đặt cơ sở dữ liệu tiếp theo .'},
 {'id': 17,
  'semester': 3,
  'name': 'Anh văn B1.1',
  'credits': 3.0,
  'elective': False,
  'prereq': [11],
  'coreq': [],
  'prereq_text': 'Anh văn A2.2',
  'coreq_text': '',
  'hours': {'lt': '3', 'da': '', 'pbl': '', 'th': '', 'tt': ''},
  'desc': 'Học phần này được thiết kế tích hợp giữa 4 kỹ năng: Nghe, Nói, Đọc, Viết và các bài tập Ngữ pháp, Từ vựng, '
          'Luyện âm. Học phần cung cấp kiến thức, kĩ năng tiếng Anh ở cấp độ tiền trung cấp. Nội dung học phần được '
          'trình bày trong 4 bài học (4 units), mỗi unit gồm các bài học nhỏ (lessons) về các kỹ năng sử dụng từ vựng; '
          'nghe hiểu (nghe hiểu ý chính và thông tin chi tiết của bài phát biểu chuẩn mực, rõ ràng về các chủ đề quen '
          'thuộc với các dạng bài tập trắc nghiệm, đúng sại, điền từ,v.v.); kĩ năng đọc hiểu (đọc hiểu ý chính của một '
          'đoạn văn hay bài báo về chủ đề như lối sống, thể thao, phương tiện giao thông, thử thách, v.v. dưới hình '
          'thức dạng trắc nghiệm, nối thông tin, trả lời ngắn); kỹ năng thảo luận, mô tả, trình bày ngắn gọn các lý '
          'do, ý kiến cá nhân trong những tình huống cụ thể; kĩ năng viết (với các bài tập ngữ pháp và viết như hoàn '
          'thành câu, viết đoạn văn ngắn, tin nhắn, email). Sau mỗi bài học, sinh viên được luyện tập, thực hành với '
          'các tài liệu cho hình thức học trực tiếp và nguồn tài nguyên thực hành trực tuyến .'},
 {'id': 18,
  'semester': 3,
  'name': 'Phương pháp tính',
  'credits': 2.0,
  'elective': False,
  'prereq': [9],
  'coreq': [],
  'prereq_text': 'Giải tích nâng cao',
  'coreq_text': '',
  'hours': {'lt': '2', 'da': '', 'pbl': '', 'th': '', 'tt': ''},
  'desc': 'Trình bày các nội dung về phần bổ túc, sai số, nội suy, tính gần đúng đạo hàm và tích phân, tính gần đúng '
          'phương trình và hệ phương trình phi tuyến, các phương pháp số của đại số tuyến tính, nghiệm gần đúng của hệ '
          'phương trình vi phân thường, giải gần đúng phương trình đạo hàm riêng bằng phương pháp số như sai phân, '
          'phương pháp phần tử hữu hạn. Trang bị cho sinh viên phương pháp giải gần đúng các bài toán hay gặp trong '
          'ngành xây dựng cơ bản.'},
 {'id': 19,
  'semester': 3,
  'name': 'Sức bền vật liệu',
  'credits': 3.0,
  'elective': False,
  'prereq': [2, 14, 1, 9],
  'coreq': [20],
  'prereq_text': 'Vật lý Cơ và Nhiệt, Cơ lý thuyết, Giải tích, Giải tích nâng cao',
  'coreq_text': 'Thí nghiệm Sức bền vật liệu',
  'hours': {'lt': '3', 'da': '', 'pbl': '', 'th': '', 'tt': ''},
  'desc': 'Học phần Sức bền vật liệu trang bị cho sinh viên khối ngành Kỹ thuật Xây dựng những kiến thức nền tảng về '
          'cơ học vật rắn biến dạng. Môn học cung cấp các phương pháp phân tích, tính toán nội lực, trạng thái ứng '
          'suất và biến dạng của các chi tiết cơ bản dạng thanh trong các trạng thái chịu lực từ cơ bản (như kéo nén '
          'đúng tâm, xoắn thuần túy, uốn phẳng) cho đến các dạng chịu lực phức tạp. Dựa trên việc xác định các đặc '
          'trưng cơ học của vật liệu và đặc trưng hình học của mặt cắt ngang, sinh viên có khả năng giải quyết toàn '
          'diện ba bài toán thiết kế kỹ thuật cốt lõi đối với kết cấu thanh thẳng: đánh giá điều kiện bền, điều kiện '
          'cứng và điều kiện ổn định.'},
 {'id': 20,
  'semester': 3,
  'name': 'Thí nghiệm Sức bền vật liệu',
  'credits': 0.5,
  'elective': False,
  'prereq': [],
  'coreq': [19],
  'prereq_text': '',
  'coreq_text': 'Sức bền vật liệu',
  'hours': {'lt': '', 'da': '', 'pbl': '', 'th': '0.5', 'tt': ''},
  'desc': 'Học phần Thí nghiệm Sức bền vật liệu là học phần thực hành cốt lõi, cung cấp cho sinh viên các kỹ năng thao '
          'tác thiết bị, đo đạc và tiến hành thí nghiệm để xác định các đặc trưng cơ học của vật liệu. Thông qua các '
          'bài thí nghiệm kinh điển như kéo, nén, uốn, xoắn và va đập, sinh viên được trực tiếp kiểm chứng các cơ sở '
          'lý thuyết đã học trong môn học Sức bền vật liệu. Môn học giúp sinh viên rèn luyện kỹ năng phân tích số liệu '
          'thực nghiệm và đánh giá thực tế khả năng chịu tải của các cấu kiện cơ bản.'},
 {'id': 21,
  'semester': 3,
  'name': 'Trắc địa',
  'credits': 2.0,
  'elective': False,
  'prereq': [9],
  'coreq': [22],
  'prereq_text': 'Giải tích nâng cao',
  'coreq_text': 'Thực tập trắc địa',
  'hours': {'lt': '2', 'da': '', 'pbl': '', 'th': '', 'tt': ''},
  'desc': 'Học phần thuộc khối kiến thức cơ sở ngành, trang bị cho người học kiến thức đại cương về bản đồ và trắc địa '
          'công trình phục vụ cho khảo sát thiết kế, thi công và quản lý các công trình thuộc ngành Kỹ thuật xây dựng '
          '– Chuyên ngành Xây dựng dân dụng và công nghiệp . Học phần gồm khối kiến thức chung về trắc địa, khối kiến '
          'thức về bản đồ và khối kiến thức về trắc địa công trình.'},
 {'id': 22,
  'semester': 3,
  'name': 'Thực tập trắc địa',
  'credits': 1.0,
  'elective': False,
  'prereq': [9],
  'coreq': [21],
  'prereq_text': 'Giải tích nâng cao',
  'coreq_text': 'Trắc địa',
  'hours': {'lt': '', 'da': '', 'pbl': '', 'th': '', 'tt': '1'},
  'desc': 'Học phần thuộc khối kiến thức cơ sở ngành, giúp cho người học áp dụng kiến thức ở Học phần Trắc địa trong '
          'việc sử dụng thiết bị đo đạc, đo vẽ bản đồ và thực hiện các công tác trắc địa trong quy hoạch, thiết kế, '
          'thi công và quản lý các công trình dân dụng và công nghiệp.'},
 {'id': 23,
  'semester': 3,
  'name': 'Thủy lực',
  'credits': 2.0,
  'elective': False,
  'prereq': [14],
  'coreq': [24],
  'prereq_text': 'Cơ lý thuyết',
  'coreq_text': 'Thí nghiệm thủy lực',
  'hours': {'lt': '2', 'da': '', 'pbl': '', 'th': '', 'tt': ''},
  'desc': 'Môn học Thủy l ực cung cấp các kiến thức chung của chất lỏng cho sinh viên các ngành Xây dựng cơ bản, ngành '
          'Kỹ thuật Cơ sở hạ tầng, ngành Kỹ thuật m ôi trường. Nội dung môn học là trang bị cho sinh viên các kiến '
          'thức về tính toán áp suất, áp lực của chất lỏng lên thành cong và thành phẳng ở trạng thái cân bằng. Môn '
          'học cũng trang bị các kiến thức của chất lỏng ở trạng thái chuyển động và vận dụng quy luật này vào các bài '
          'toán dòng chảy qua lổ, vòi và đường ống.'},
 {'id': 24,
  'semester': 3,
  'name': 'Thí nghiệm thủy lực',
  'credits': 0.5,
  'elective': False,
  'prereq': [],
  'coreq': [23],
  'prereq_text': '',
  'coreq_text': 'Thủy lực',
  'hours': {'lt': '', 'da': '', 'pbl': '', 'th': '0.5', 'tt': ''},
  'desc': 'Trên cơ sở lý thuyết về tính áp suất thủy tĩnh và tổn thất trong đường ống (dọc đường và cục bộ), …sinh '
          'viên thực hành để hiểu rõ hơn phần lý thuyết thủy lực cơ sở cũng như nắm bắt được kỹ năng sử dụng phần mềm '
          'và thực hành trong thực tế.'},
 {'id': 25,
  'semester': 4,
  'name': 'Phân tích và thiết kế thuật toán trong xây dựng',
  'credits': 2.0,
  'elective': False,
  'prereq': [12],
  'coreq': [],
  'prereq_text': 'Ngôn ngữ lập trình trong xây dựng',
  'coreq_text': '',
  'hours': {'lt': '2', 'da': '', 'pbl': '', 'th': '', 'tt': ''},
  'desc': 'Học phần cung cấp các kiến thức cơ bản và nâng cao về thuật toán trong tin học, bao gồm khái niệm, phương '
          'pháp biểu diễn và kỹ thuật phân tích độ phức tạp của thuật toán. Sinh viên được hướng dẫn cách đánh giá '
          'hiệu năng và lựa chọn thuật toán phù hợp cho từng bài toán cụ thể. Bên cạnh đó, học phần tập trung phân '
          'tích và ứng dụng các thuật toán cơ bản vào giải quyết các bài toán trong lĩnh vực xây dựng như tính toán, '
          'thiết kế và tối ưu các cấu kiện công trình, các giải pháp trong xây dựng công trình đô thị, … . Các thuật '
          'toán/chiến lược thiết kế thuật toán được giới thiệu gồm: sắp xếp, tìm kiếm, đệ quy, vét cạn, quay lui, chia '
          'để trị, quy hoạch động và thuật toán tham lam.'},
 {'id': 26,
  'semester': 4,
  'name': 'Kinh tế chính trị Mác - Lênin',
  'credits': 2.0,
  'elective': False,
  'prereq': [5],
  'coreq': [],
  'prereq_text': 'Triết học Mác - Lênin',
  'coreq_text': '',
  'hours': {'lt': '2', 'da': '', 'pbl': '', 'th': '', 'tt': ''},
  'desc': 'Học phần được kết cấu thành 2 phần chính: - Một là, nghiên cứu các vấn đề kinh tế chính trị của phương thức '
          'sản xuất tư bản chủ nghĩa trong cả hai giai đoạn là tự do cạnh tranh và giai đoạn độc quyền. - Hai là, '
          'nghiên cứu các vấn đề về kinh tế thị trường định hướng xã hội chủ nghĩa và các quan hệ lợi ích kinh tế ở '
          'Việt Nam; Công nghiệp hóa, hiện đại hóa và hội nhập kinh tế quốc tế của Việt Nam.'},
 {'id': 27,
  'semester': 4,
  'name': 'Ứng dụng xác suất và thống kê trong xây dựng',
  'credits': 2.0,
  'elective': False,
  'prereq': [9],
  'coreq': [],
  'prereq_text': 'Giải tích nâng cao',
  'coreq_text': '',
  'hours': {'lt': '2', 'da': '', 'pbl': '', 'th': '', 'tt': ''},
  'desc': 'Học phần Ứng dụng x ác suất và Thống kê trong xây dựng (Probability and Statistics in Civil Engineering) '
          'cung cấp cho sinh viên các kiến thức cơ bản về xác suất và thống kê cùng các phương pháp phân tích dữ liệu '
          'nhằm giải quyết các bài toán trong lĩnh vực kỹ thuật xây dựng và trí tuệ nhân tạo (học máy và học sâu) . '
          'Nội dung học phần bao gồm các khái niệm và phương pháp như mô hình xác suất, biến ngẫu nhiên, các phân bố '
          'xác suất, phân tích dữ liệu, suy luận thống kê, cũng như phân tích hồi quy và tương quan. Bên cạnh nền tảng '
          'lý thuyết, học phần còn giới thiệu và minh họa các ứng dụng quan trọng của xác suất và thống kê trong thực '
          'tiễn kỹ thuật xây dựng, chẳng hạn như phân tích dữ liệu thí nghiệm vật liệu xây dựng, dự báo thủy văn, phân '
          'tích rủi ro công trình, đánh giá độ tin cậy kết cấu và mô phỏng Monte Carlo trong phân tích kỹ thuật. Trong '
          'quá trình học tập, sinh viên được hướng dẫn sử dụng các công cụ tính toán và phân tích dữ liệu phổ biến như '
          'Excel, Matlab; Python hoặc R để xử lý dữ liệu kỹ thuật, mô phỏng các hiện tượng ngẫu nhiên và hỗ trợ ra '
          'quyết định trong thiết kế và quản lý công trình xây dựng. .'},
 {'id': 28,
  'semester': 4,
  'name': 'Môi trường và phát triển bền vững',
  'credits': 2.0,
  'elective': False,
  'prereq': [],
  'coreq': [],
  'prereq_text': '',
  'coreq_text': '',
  'hours': {'lt': '2', 'da': '', 'pbl': '', 'th': '', 'tt': ''},
  'desc': 'Học phần này cung cấp cho sinh viên các hiểu biết cơ bản về môi trường, tài nguyên , hệ sinh thái , khái '
          'niệm về ô nhiễm môi trường ( không khí, nước, đất ), ô nhiễm chất thải rắn và một số loại ô nhiễm khác như '
          'tiếng ồn, nhiệt ; biết được các nguồn gây ô nhiễm, các tác nhân gây ô nhiễm môi trường ; trên cơ sở đó đề '
          'xuất được những giải pháp xử lý, giảm thiểu ô nhiễm môi trường để có những hành động phù hợp trong cuộc '
          'sống hàng ngày. Ngoài ra, học phần này còn giúp sinh viên nắm được các khái niệm, nguyên tắc và giải pháp '
          'để đạt tới sự hài hòa về môi trường và phát triển , hướng tới phát triển kinh tế xã hội theo hướng bền '
          'vững.'},
 {'id': 29,
  'semester': 4,
  'name': 'Cơ học kết cấu 1',
  'credits': 2.0,
  'elective': False,
  'prereq': [14, 19],
  'coreq': [],
  'prereq_text': 'Cơ lý thuyết, Sức bền Vật liệu',
  'coreq_text': '',
  'hours': {'lt': '2', 'da': '', 'pbl': '', 'th': '', 'tt': ''},
  'desc': 'Cơ học k ết cấu 1 là học phần C ơ sở ngành dành cho sinh viên thuộc các ngành Kỹ thuật Xây dựng công trình '
          '. Học phần nà y cung cấp cho sinh viên những kiến thức thiết yếu để giải quyết các bài toán kết cấu trong '
          'thực tế bao gồm các khâu: thiết kế, thẩm định và thi công công trình . Nội dung của học phần trang bị cho '
          'sinh viên khả năng phân tích tính chất chịu lực của hệ kết cấu, kỹ năng tính toán nội lực trong các hệ kết '
          'cấu tĩnh định chịu tác dụng của các nguyên nhân tải trọng bất động và di động. Có k iến thức, kỹ năng và '
          'thái độ tốt trong học phần này giúp sinh viên học tốt các học phần Chuyên ngành trong các năm học tiếp theo '
          '.'},
 {'id': 30,
  'semester': 4,
  'name': 'Cơ học đất',
  'credits': 2.0,
  'elective': False,
  'prereq': [19],
  'coreq': [31],
  'prereq_text': 'Sức bền vật liệu',
  'coreq_text': 'Thí nghiệm cơ học đất',
  'hours': {'lt': '2', 'da': '', 'pbl': '', 'th': '', 'tt': ''},
  'desc': 'Học phần Cơ học đất cung cấp cho n gười học các kiến thức như: Sự hình thành của đất ; thành phần '
          'cấu tạo và tính chất cơ lý của đất; phương pháp thí nghiệm xác định chỉ tiêu cơ lý thông thường của '
          'đất đá ở trong phòng thí nghiệm và xử lý tính toán kết quả thí nghiệm ; xác định ứng suất trong nền '
          'đất khi móng chịu tải trọng ngoài tác dụng và trọng lượng bản thân ; Tính chất biến dạng của '
          'đất, tính toán độ lún cho nền móng công trình và độ lún theo thời gian; Sức chống cắt của đất, t '
          'ính toán xác định sức chịu tải cho nền đất, sự ổn định của mái dốc và tính toán áp lực '
          'đất tác dụng lên tường chắn.'},
 {'id': 31,
  'semester': 4,
  'name': 'Thí nghiệm cơ học đất',
  'credits': 0.5,
  'elective': False,
  'prereq': [],
  'coreq': [30],
  'prereq_text': '',
  'coreq_text': 'Cơ học đất',
  'hours': {'lt': '', 'da': '', 'pbl': '', 'th': '0.5', 'tt': ''},
  'desc': 'Học phần giúp sinh viên làm quen với quá trình tiến hành một thí nghiệm thông qua các bài thực hành , t '
          'rang bị cho sinh viên những kiến thức cơ bản nhất về thí nghiệm các chỉ tiêu cơ lý của đất . Từ đó sinh '
          'viên hiểu rõ hơn công tác thí nghiệm trong phòng, phương pháp xử lý tính toán kết quả thí nghiệm và phân '
          'loại được mẫu đất . Ngoài ra, học phần sẽ củng cố kiến thức lý thuyết, hình thành kĩ năng thí nghiệm, thực '
          'hành, phát triển kĩ năng làm việc nhóm .'},
 {'id': 32,
  'semester': 4,
  'name': 'Vật liệu xây dựng',
  'credits': 2.0,
  'elective': False,
  'prereq': [19],
  'coreq': [33],
  'prereq_text': 'Sức bền vật liệu',
  'coreq_text': 'Thí nghiệm vật liệu xây dựng',
  'hours': {'lt': '2', 'da': '', 'pbl': '', 'th': '', 'tt': ''},
  'desc': 'Học phần Vật liệu xây dựng thuộc khối kiến thức cơ sở ngành . Học phần trang bị cho SV các kiến thức nền '
          'tảng về các loại vật liệu chủ yếu sử dụng trong xây dựng như vật liệu đá thiên nhiê n , gốm xây dựng, chất '
          'kết dính, bê tông dùng chất kết dính vô cơ, vữa xây dựng và gỗ xây dựng. Nội dung chính sẽ tập trung vào '
          'thành phần, cấu trúc , tính chất , nguyên tắc sản xuất VLXD, từ đó người học biết đánh giá chất lượng , lựa '
          'chọn loại VLXD sử dụng thích hợp cho từng công trình xây dựng , có thể đưa ra các giải pháp VLXD đảm bảo '
          'các yêu cầu về tính năng kỹ thuật và hiệu quả kinh tế.'},
 {'id': 33,
  'semester': 4,
  'name': 'Thí nghiệm vật liệu xây dựng',
  'credits': 0.5,
  'elective': False,
  'prereq': [],
  'coreq': [32],
  'prereq_text': '',
  'coreq_text': 'Vật liệu xây dựng',
  'hours': {'lt': '', 'da': '', 'pbl': '', 'th': '0.5', 'tt': ''},
  'desc': 'Học phần Thí nghiệm Vật liệu xây dựng giới thiệu kiến thức về phương pháp thử các tính chất cơ lý; các '
          'phương pháp đánh giá chất lượng của các loại vật liệu chủ yếu dùng trong xây dựng; cách sử dụng và vận hành '
          'các thiết bị thí nghiệm. Đây là cơ sở cho những môn học thuộc nhóm chuyên ngành Xây dựng như Nền móng, Kết '
          'cấu Bê tông cốt thép, Công nghệ bê tông, Kỹ thuật sản xuất chất kết dính, Công nghệ gốm xây dựng, Kiểm định '
          'và thí nghiệm công trình, Thí nghiệm Đường, Khai thác và thí nghiệm Cầu. Ngoài ra, những kiến thức về thí '
          'nghiệm VLXD cung cấp trong học phần còn phục vụ cho kỹ sư xây dựng hoạt động trong các lĩnh vực thiết kế, '
          'thi công, tư vấn giám sát, kiểm định.'},
 {'id': 34,
  'semester': 4,
  'name': 'Thủy lực công trình',
  'credits': 2.0,
  'elective': False,
  'prereq': [23],
  'coreq': [],
  'prereq_text': 'Thủy lực',
  'coreq_text': '',
  'hours': {'lt': '2', 'da': '', 'pbl': '', 'th': '', 'tt': ''},
  'desc': 'Học phần cung cấp cho sinh viên các kiến thức cơ bản về thủy lực dòng chảy trong kênh hở, sông thiên nhiên '
          'và qua công trình thủy lợi, bao gồm các quy luật của dòng chảy đều, và dòng không đều biến đổi dần. Trên cơ '
          'sở đó, học phần trình bày các phương pháp tính toán dòng chảy mặt qua công trình (đập tràn, cống, nền và '
          'thân công trình) và dòng thấm. Đồng thời, sinh viên được học và vận dụng các giải pháp kỹ thuật nối tiếp và '
          'tiêu năng dòng chảy, cũng như thực hiện tính toán, thiết kế sơ bộ một số công trình thủy lợi.'},
 {'id': 35,
  'semester': 5,
  'name': 'Tư tưởng Hồ Chí Minh',
  'credits': 2.0,
  'elective': False,
  'prereq': [5],
  'coreq': [],
  'prereq_text': 'Triết học Mác - Lênin',
  'coreq_text': '',
  'hours': {'lt': '2', 'da': '', 'pbl': '', 'th': '', 'tt': ''},
  'desc': 'Tư tưởng Hồ Chí Minh là môn khoa học cung cấp những kiến thức cơ bản về tư tưởng của Chủ tịch Hồ Chí Minh '
          'với ý nghĩa là sự vận dụng sáng tạo lý luận chủ nghĩa Mác Lênin vào điều kiện cụ thể Việt Nam, đồng thời là '
          'cơ sở lý luận trực tiếp trong việc hoạch định đường lối cách mạng Việt Nam từ 1930 đến nay. Học phần này '
          'giúp sinh viên hiểu được một cách tương đối đầy đủ và có hệ thống về bối cảnh lịch sử - xã hội, cơ sở hình '
          'thành, phát triển của tư tưởng Hồ Chí Minh; Các nội dung cơ bản của tư tưởng Hồ Chí Minh về: Vấn đề dân tộc '
          'và cách mạng giải phóng dân tộc; về CNXH; …. Trên cơ sở đó góp phần giúp sinh viên hình thành lập trường '
          'khoa học và cách mạng, kiên định con đường mà Chủ tịch Hồ Chí Minh và Đảng ta đã lựa chọn.'},
 {'id': 36,
  'semester': 5,
  'name': 'Thực hành lập trình trên môi trường Windows',
  'credits': 1.0,
  'elective': False,
  'prereq': [16],
  'coreq': [],
  'prereq_text': 'Cấu trúc và cơ sở dữ liệu trong xây dựng',
  'coreq_text': '',
  'hours': {'lt': '', 'da': '', 'pbl': '', 'th': '1', 'tt': ''},
  'desc': 'Học phần thực hành này trang bị cho sinh viên kỹ năng thao tác trực tiếp trên môi trường Visual Studio bằng '
          'ngôn ngữ C#. Sinh viên sẽ thực hành thiết kế giao diện Windows Form từ cơ bản đến nâng cao, đồng thời thao '
          'tác kết nối, truy vấn và xử lý dữ liệu qua nền tảng ADO.NET. Thông qua các bài thực hành trên máy tính, '
          'sinh viên hình thành kỹ năng viết mã lệnh (coding), gỡ lỗi (debugging) và tự phát triển các công cụ phần '
          'mềm ứng dụng nhỏ phục vụ cho công tác chuyên môn của ngành Tin học xây dựng .'},
 {'id': 37,
  'semester': 5,
  'name': 'Phương pháp Phần tử hữu hạn',
  'credits': 2.0,
  'elective': False,
  'prereq': [18],
  'coreq': [],
  'prereq_text': 'Phương pháp tính',
  'coreq_text': '',
  'hours': {'lt': '2', 'da': '', 'pbl': '', 'th': '', 'tt': ''},
  'desc': 'Học phần trang bị cho sinh viên các kiến thức cơ sở về phương pháp phần tử hữu hạn, áp dụng trong tính toán '
          'các bài toán cơ học , đặc biệt là giải các bài toán tính toán các kết cấu vật rắn biến dạng. Nội dung học '
          'phần bao gồm gồm cơ sở lý thuyết, giải thuật, lập trình tính toán các bài toán kết cấu .'},
 {'id': 38,
  'semester': 5,
  'name': 'Phương pháp nghiên cứu khoa học',
  'credits': 2.0,
  'elective': False,
  'prereq': [27],
  'coreq': [],
  'prereq_text': 'Ứng dụng xác suất và thống kê trong xây dựng',
  'coreq_text': '',
  'hours': {'lt': '2', 'da': '', 'pbl': '', 'th': '', 'tt': ''},
  'desc': 'Học phần Phương pháp nghiên cứu khoa học (NCKH) trang bị cho các sinh viên những kiến thức bổ trợ về phương '
          'pháp nghiên cứu khoa học và kỹ năng viết một báo cáo khoa học. Học phần này rất có ý nghĩa cho sinh viết '
          'luận văn tốt nghiệp hoặc thực hiện đề tài nghiên cứu khoa học. Các hoạt động giảng day trên lớp sẽ kết hợp '
          'giữa lý thuyết và bài tập nhóm để người học tiếp thu và thực hành dễ dàng.'},
 {'id': 39,
  'semester': 5,
  'name': 'Cơ học kết cấu 2',
  'credits': 2.0,
  'elective': False,
  'prereq': [29],
  'coreq': [],
  'prereq_text': 'Cơ học kết cấu 1',
  'coreq_text': '',
  'hours': {'lt': '2', 'da': '', 'pbl': '', 'th': '', 'tt': ''},
  'desc': 'Học phần Cơ học kết cấu 2 cung cấp cho sinh viên các kiến thức và phương pháp phân tích nội lực và chuyển '
          'vị trong hệ kết cấu thanh. Nội dung học phần tập trung vào ba vấn đề chính: (1) xác định chuyển vị trong hệ '
          'thanh thẳng tĩnh định dựa trên các khái niệm về biến dạng và phương pháp nhân biểu đồ Vê-rê-sa-ghin; (2) '
          'phân tích hệ siêu tĩnh bằng phương pháp lực, bao gồm xác định bậc siêu tĩnh, thiết lập và giải hệ phương '
          'trình chính tắc để xác định nội lực và chuyển vị; (3) phân tích hệ siêu tĩnh – siêu động bằng phương pháp '
          'chuyển vị, bao gồm xác định bậc siêu động , thiết lập và giải hệ phương trình chính tắc để xác định nội lực '
          'và chuyển vị, đồng thời nghiên cứu hệ dầm liên tục cùng biểu đồ bao nội lực. Học phần được giảng dạy thông '
          'qua bài giảng lý thuyết, bài tập ứng dụng, hoạt động tự học và các hình thức đánh giá giữa kỳ, cuối kỳ, '
          'nhằm giúp sinh viên phát triển năng lực phân tích và giải quyết các bài toán kết cấu trong kỹ thuật xây '
          'dựng.'},
 {'id': 40,
  'semester': 5,
  'name': 'Nền và móng',
  'credits': 2.0,
  'elective': False,
  'prereq': [30],
  'coreq': [],
  'prereq_text': 'Cơ học đất',
  'coreq_text': '',
  'hours': {'lt': '2', 'da': '', 'pbl': '', 'th': '', 'tt': ''},
  'desc': 'Học phần Nền và Móng là một trong những học phần chuyên ngành cần thiết đối với sinh viên ngành xây dựng. H '
          'ọc phần này cung cấp những khái niệm, cơ sở thiết kế và cấu tạo các loại móng trong công trình xây dựng, từ '
          'đó giúp sinh viên nhận biết, phân biệt, lựa chọn, phân tích, đánh giá các giải pháp xây dựng móng (móng '
          'nông, móng sâu) cũng như các biện pháp xử lý, gia cố khi xây dựng công trình trên nền đất yếu. Đây là học '
          'phần trang bị những kiến thức quan trọng về nền và móng công trình để sinh viên các ngành xây dựng có thể '
          'vận dụng và kết nối kiến thức với các học phần khác trong chương trình đạo tạo kỹ sư xây dựng.'},
 {'id': 41,
  'semester': 5,
  'name': 'Đồ án Nền và móng',
  'credits': 1.0,
  'elective': False,
  'prereq': [],
  'coreq': [40],
  'prereq_text': '',
  'coreq_text': 'Nền và móng',
  'hours': {'lt': '', 'da': '1', 'pbl': '', 'th': '', 'tt': ''},
  'desc': 'Học phần PBL Nền và móng l à học phần cơ sở ngành và một phần chuyên ngành. Học phần trang bị cho người học '
          'kiến thức về việc tập hợp số liệu địa chất, tải trọng và lựa chọn vật liệu phục vụ thiết kế nền móng . N '
          'gười học phân tích và đề xuất phương án, tính toán thiết kế nền móng bao gồm móng nông và móng sâu cho công '
          'trình xây dựng theo các tiêu chuẩn hiện hàn h. Học phần có sự liên hệ đến các học phần khác trong việc tính '
          'toán thiết kế công trình trên nền đất, công trình ngầm và đồ án tốt nghiệp .'},
 {'id': 42,
  'semester': 5,
  'name': 'Kết cấu bê tông cốt thép - phần cơ bản',
  'credits': 3.0,
  'elective': False,
  'prereq': [29],
  'coreq': [],
  'prereq_text': 'Cơ học kết cấu 1',
  'coreq_text': '',
  'hours': {'lt': '3', 'da': '', 'pbl': '', 'th': '', 'tt': ''},
  'desc': 'Học phần này giúp sinh viên hiểu được khái quát chung về vật liệu bê tông cốt thép, các tính '
          'chất cơ lý của vật liệu, sự làm việc chung giữa bê tông và cốt thép. Bên cạnh đó, học phần '
          'trang bị cho sinh viên những nguyên lý tính toán và cấu tạo các cấu kiện cơ bản bê tông cốt thép theo '
          'các trạng thái giới hạn khác nhau. Kết thúc học phần, sinh viên có thể thiết kế các cấu kiện cơ bản bê tông '
          'cốt thép.'},
 {'id': 43,
  'semester': 5,
  'name': 'Đồ án Kết cấu bê tông cốt thép',
  'credits': 1.0,
  'elective': False,
  'prereq': [],
  'coreq': [42],
  'prereq_text': '',
  'coreq_text': 'KC BTCT - phần cơ bản',
  'hours': {'lt': '', 'da': '1', 'pbl': '', 'th': '', 'tt': ''},
  'desc': 'Thiết kế sàn sườn bê tông cốt thép toàn khối, bao gồm lựa chọn phương án kết cấu sàn, xác định sơ bộ kích '
          'thước các cấu kiện; xác định các tải trọng thường xuyên và tải trọng tạm thời tác dụng lên bản và dầm; phân '
          'tích và tổ hợp nội lực; tính toán và bố trí cốt thép chịu lực và cấu tạo. K ết quả thiết kế được thể hiện '
          'trong thuyết minh và trên bản vẽ kỹ thuật.'},
 {'id': 44,
  'semester': 5,
  'name': 'Thủy văn',
  'credits': 2.0,
  'elective': False,
  'prereq': [27],
  'coreq': [],
  'prereq_text': 'Ứng dụng XS và TK trong xây dựng',
  'coreq_text': '',
  'hours': {'lt': '2', 'da': '', 'pbl': '', 'th': '', 'tt': ''},
  'desc': 'Học phần cung cấp kiến thức cơ bản về các quá trình thủy văn, phương pháp phân tích số liệu khí tượng – '
          'thủy văn và tính toán các đặc trưng thủy văn phục vụ thiết kế công trình , quy hoạch quản lý hệ thống nguồn '
          'nước, thiết kế công trình cầu - đường, thiết kế cơ sở hạ tầng , thiết kế cấp thoát nước công trình dân dụng '
          'và công nghiệp , thiết kế quy hoạch đô thị, và quản lý rủi ro thiên tai v.v …'},
 {'id': 45,
  'semester': 6,
  'name': 'Pháp luật đại cương',
  'credits': 2.0,
  'elective': False,
  'prereq': [],
  'coreq': [],
  'prereq_text': '',
  'coreq_text': '',
  'hours': {'lt': '2', 'da': '', 'pbl': '', 'th': '', 'tt': ''},
  'desc': 'Học phần Pháp luật đại cương được thiết kế nhằm cung cấp cho người học những kiến thức cơ bản nhất về Nhà '
          'nước và Pháp luật. Nội dung cơ bản của học phần bao gồm: Những vấn đề chung về Nhà nước và pháp luật như Bộ '
          'máy nhà nước, Quy phạm pháp luật và Quan hệ pháp luật, Vi phạm pháp luật… Ngoài ra, học phần cũng cung cấp '
          'cho người học một số kiến thức cơ bản về phòng chống tham nhũng.'},
 {'id': 46,
  'semester': 6,
  'name': 'Tư duy khởi nghiệp và đổi mới sáng tạo',
  'credits': 2.0,
  'elective': False,
  'prereq': [4, 7],
  'coreq': [],
  'prereq_text': 'Nhập môn ngành, Nhập môn công nghệ số và ứng dụng trí tuệ nhân tạo',
  'coreq_text': '',
  'hours': {'lt': '2', 'da': '', 'pbl': '', 'th': '', 'tt': ''},
  'desc': 'Môn học trang bị cho sinh viên chương trình kỹ sư nền tảng tư duy và bộ công cụ để nhận diện vấn đề có giá '
          'trị trong bối cảnh nghề nghiệp kỹ thuật, hình thành ý tưởng giải pháp dựa trên khoa học–công nghệ, mô hình '
          'hóa cách tạo giá trị và đề xuất kế hoạch thử nghiệm ban đầu. Nội dung học phần tập trung vào: tư duy khởi '
          'nghiệp và đổi mới sáng tạo trong kỷ nguyên số ; năng lực cốt lõi của nhà khởi nghiệp/kỹ sư đổi mới; phương '
          'pháp đổi mới sáng tạo và đánh giá ý tưởng; mô hình kinh doanh Canvas; thiết kế sản phẩm khả dụng tối thiểu '
          '(MVP) và kế hoạch thử nghiệm/đo lường ở mức cơ bản; giới thiệu hệ sinh thái khởi nghiệp và định hướng nghề '
          'nghiệp gắn với đổi mới và chuyển đổi xanh. Kết thúc học phần, sinh viên có thể trình bày một đề xuất dự án '
          'đổi mới/khởi nghiệp ở mức cơ bản kèm mô hình kinh doanh và kế hoạch thử nghiệm/MVP.'},
 {'id': 47,
  'semester': 6,
  'name': 'Kết cấu nhà bê tông cốt thép',
  'credits': 2.0,
  'elective': False,
  'prereq': [42],
  'coreq': [],
  'prereq_text': 'Kết cấu bê tông cốt thép - phần cơ bản',
  'coreq_text': '',
  'hours': {'lt': '2', 'da': '', 'pbl': '', 'th': '', 'tt': ''},
  'desc': 'Học phần trang bị cho sinh viên kiến thức và kỹ năng lập phương án kết cấu, tính toán nội lực và thiết kế '
          'kết cấu các bộ phận của công trình dân dụng bằng bê tông cốt thép bao gồm kết cấu sàn, cầu thang, kết cấu '
          'khung không gian, kết cấu móng.'},
 {'id': 48,
  'semester': 6,
  'name': 'Công trình thủy',
  'credits': 3.0,
  'elective': False,
  'prereq': [23],
  'coreq': [],
  'prereq_text': 'Thủy lực',
  'coreq_text': '',
  'hours': {'lt': '3', 'da': '', 'pbl': '', 'th': '', 'tt': ''},
  'desc': 'Môn học cung cấp cho sinh viên những hiểu biết chung về các loại công trình thuỷ, khả năng phân tích chọn '
          'các giải pháp công trình, phương án tuyến, phương án về h́ình thức kết cấu. Tính toán các xác định các '
          'thông số cơ bản của công trình. Thiết kế cấu tạo, tính toán thuỷ lực công trình, kiểm tra thấm, ổn định và '
          'tính toán kết cấu, nền móng các hạng mục trong hệ thống (đập, công trình tràn xă lũ, cống và công trình lấy '
          'nước, đường hầm thủy công, các công trình trên đường dẫn).'},
 {'id': 49,
  'semester': 6,
  'name': 'Đồ án Công trình thủy',
  'credits': 1.0,
  'elective': False,
  'prereq': [],
  'coreq': [48],
  'prereq_text': '',
  'coreq_text': 'Công trình thủy',
  'hours': {'lt': '', 'da': '1', 'pbl': '', 'th': '', 'tt': ''},
  'desc': 'Môn học cung cấp cho sinh viên khả năng vận dụng các kiến thức về lựa chọn biện pháp công trình, đề xuất '
          'phương án tuyến, phương án về hình thức kết cấu để bố trí tổng thể các hạng mục công trình đầu mối. Thiết '
          'kế cấu tạo các bộ phận, tính thủy lực, kiểm tra thấm, ổn định, kết cấu của một trong số các hạng mục (theo '
          'nhóm): Cống hở, công trình đập đất, đập bê tông trọng lực, đập tràn xã lũ hoặc cống ngầm lấy nước dưới đập '
          '- Các vấn đề tính toán thiết kế được định hướng tự động hoá trên máy tính và sử dụng các phần mềm thiết '
          'kế.'},
 {'id': 50,
  'semester': 6,
  'name': 'Cơ sở thiết kế kết cấu thép',
  'credits': 2.0,
  'elective': False,
  'prereq': [19],
  'coreq': [],
  'prereq_text': 'Sức bền vật liệu',
  'coreq_text': '',
  'hours': {'lt': '2', 'da': '', 'pbl': '', 'th': '', 'tt': ''},
  'desc': 'Học phần cung cấp cho sinh viên kiến thức lý thuyết cơ sở về vật liệu thép, quy trình, cách thiết kế, tính '
          'toán kết cấu thép theo tiêu chuẩn hiện hành. Giúp sinh viên biết cách tính toán các liên kết kết cấu thép, '
          'tính toán và kiểm tra các cấu kiện cơ bản như dầm, cột, dàn.'},
 {'id': 51,
  'semester': 6,
  'name': 'Phần mềm trong xây dựng',
  'credits': 2.0,
  'elective': False,
  'prereq': [29],
  'coreq': [],
  'prereq_text': 'Cơ học kết cấu 1',
  'coreq_text': '',
  'hours': {'lt': '2', 'da': '', 'pbl': '', 'th': '', 'tt': ''},
  'desc': 'Môn học trang bị cho sinh viên những kiến thức về thuật giải các bài toán ứng dụng trong chuyên môn. Vận '
          'dụng kiến thức về công nghệ thông tin phát triển các phần mềm chuyên dụng. Khai thác các phần mềm chuyên '
          'ngành phục vụ cho công tác thiết kế, thi công công trình xây dựng cơ bản như chương trình tính kết cấu, ổn '
          'định, thấm … cho các công trình xây dựng. Hỗ trợ kiến thức, kỹ năng cho sinh viên thực hiện các Đồ án liên '
          'môn trong chương trình đào tạo.'},
 {'id': 52,
  'semester': 6,
  'name': 'Ứng dụng GIS trong xây dựng',
  'credits': 2.0,
  'elective': False,
  'prereq': [21],
  'coreq': [],
  'prereq_text': 'Trắc địa',
  'coreq_text': '',
  'hours': {'lt': '2', 'da': '', 'pbl': '', 'th': '', 'tt': ''},
  'desc': 'Môn học cung cấp cho sinh viên những hiểu biết chung về hệ thống thông tin địa lý (GIS) và hệ thống định vị '
          'toàn cầu (GPS), nguyên lý hoạt động cũng như khả năng ứng dụng của GIS và GPS trong các lĩnh vực, đặt biệt '
          'trong lĩnh vực xây dựng. Môn học cung cấp cho sinh viên những kỹ năng cơ bản để xây dựng, quản lý cũng như '
          'khai thác hệ thống GIS, từ đó giúp sinh viên có thể tiếp cận giải quyết các vấn đề thực tế trên nền tảng '
          'GIS.'},
 {'id': 53,
  'semester': 6,
  'name': 'Thực tập nhận thức',
  'credits': 1.0,
  'elective': False,
  'prereq': [4],
  'coreq': [],
  'prereq_text': 'Nhập môn ngành',
  'coreq_text': '',
  'hours': {'lt': '', 'da': '', 'pbl': '', 'th': '', 'tt': '1'},
  'desc': 'Học phần trang bị cho sinh viên ngành Kỹ thuật xây dựng , chuyên ngành Tin học xây dựng các kiến thức về '
          'các công trình thực tế bao gồm thiêt kế , thi công, quản lý , vận hành các công trình xây dựng trong lĩnh '
          'vực : công trình dân dụng , công trình giao thông , công trình thủy , hạ tầng kỹ thuật thông qua các hoạt '
          'động ngoại khóa tại các công ty xây dựng , các công trình đang xây dựng ở trên địa bàn miền trung , tây '
          'nguyên .'},
 {'id': 54,
  'semester': 7,
  'name': 'Phát triển phần mềm mã nguồn mở',
  'credits': 2.0,
  'elective': False,
  'prereq': [36],
  'coreq': [],
  'prereq_text': 'Thực hành lập trình trên môi trường Windows',
  'coreq_text': '',
  'hours': {'lt': '2', 'da': '', 'pbl': '', 'th': '', 'tt': ''},
  'desc': 'Học phần trang bị cho người học kiến thức nền tảng về các khái niệm, hệ thống quản lý dự án và các loại '
          'giấy phép bản quyền của phần mềm mã nguồn mở. Bên cạnh đó, người học sẽ được hướng dẫn ứng dụng bộ công cụ '
          'Visual Studio và thư viện Revit API (thông qua ngôn ngữ lập trình C#) nhằm phát triển các tiện ích bổ trợ '
          '(Add-ins) mã nguồn mở. Sau khi hoàn thành học phần, người học sẽ hình thành năng lực tự lập trình và xây '
          'dựng các công cụ phần mềm giúp tự động hóa quá trình tính toán, thiết kế, đáp ứng các bài toán thực tế '
          'trong lĩnh vực xây dựng .'},
 {'id': 55,
  'semester': 7,
  'name': 'Kỹ thuật thi công',
  'credits': 3.0,
  'elective': False,
  'prereq': [47],
  'coreq': [],
  'prereq_text': 'Kết cấu nhà bê tông cốt thép',
  'coreq_text': '',
  'hours': {'lt': '3', 'da': '', 'pbl': '', 'th': '', 'tt': ''},
  'desc': 'Học phần K ỹ thuật thi công sẽ cung cấp cho sinh viên các kiến thức về tính toán khối lượng và lập biện '
          'pháp kỹ thuật thi công cho các công trình xây dựng cơ bản bao gồm: Công tác chuẩn bị xây dựng, công tác '
          'đất, đá; công tác xây gạch, đá; công tác bê tông và bê tông cốt thép. Bên cạnh đó, học phần này còn cung '
          'cấp cho sinh viên kỹ năng ứng dụng công nghệ thông tin để giải quyết công việc trong nội dung học phần.'},
 {'id': 56,
  'semester': 7,
  'name': 'Kinh tế xây dựng',
  'credits': 2.0,
  'elective': False,
  'prereq': [47],
  'coreq': [],
  'prereq_text': 'Kết cấu nhà bê tông cốt thép',
  'coreq_text': '',
  'hours': {'lt': '2', 'da': '', 'pbl': '', 'th': '', 'tt': ''},
  'desc': 'Học phần Kinh tế xây dựng cung cấp cho sinh viên các kiến thức nền tảng và công cụ phân tích kinh tế trong '
          'hoạt động đầu tư xây dựng công trình. Nội dung học phần bao gồm: các quy luật kinh tế trong đầu tư xây '
          'dựng; cơ cấu chi phí và nguồn vốn; các phương pháp phân tích, đánh giá hiệu quả tài chính – kinh tế – xã '
          'hội của dự án; lập dự toán công trình theo quy định hiện hành. Học phần đồng thời rèn luyện kỹ năng sử dụng '
          'các phần mềm hỗ trợ như Crystal Ball (phân tích rủi ro) và F1 (lập dự toán). Thông qua học phần này, sinh '
          'viên có khả năng vận dụng các công cụ kinh tế để phân tích, đánh giá chi phí, góp phần nâng cao hiệu quả '
          'của dự án xây dựng.'},
 {'id': 57,
  'semester': 7,
  'name': 'Công nghệ BIM trong xây dựng',
  'credits': 3.0,
  'elective': False,
  'prereq': [47],
  'coreq': [],
  'prereq_text': 'Kết cấu nhà BTCT',
  'coreq_text': '',
  'hours': {'lt': '3', 'da': '', 'pbl': '', 'th': '', 'tt': ''},
  'desc': 'Học phần trang bị cho sinh viên chuyên ngành Tin học xây dựng nền tảng tri thức và kỹ năng thực hành về Mô '
          'hình thông tin công trình - BIM (Building Information Modeling) . Nội dung môn học tập trung phân tích vai '
          'trò và cách thức ứng dụng công nghệ BIM để giải quyết các vấn đề kỹ thuật phục vụ đa dạng chủ thể trong dự '
          'án: chủ đầu tư, tư vấn thiết kế, quản lý dự án, thi công và quản lý vận hành . Sau khi hoàn thành học phần, '
          'người học có khả năng vận dụng linh hoạt công nghệ số vào thực tiễn công việc của kỹ sư xây dựng ở nhiều vị '
          'trí khác nhau, đáp ứng trực tiếp yêu cầu chuyển đổi số của dự án .'},
 {'id': 58,
  'semester': 7,
  'name': 'Công trình giao thông',
  'credits': 3.0,
  'elective': False,
  'prereq': [30, 29],
  'coreq': [],
  'prereq_text': 'Cơ học đất; Cơ học kết cấu 1',
  'coreq_text': '',
  'hours': {'lt': '3', 'da': '', 'pbl': '', 'th': '', 'tt': ''},
  'desc': 'Học phần này cung cấp: Các khái niệm cơ bản về các công trình nhân tạo trên đường (cầu, đường và cống); Cấu '
          'tạo các bộ phận chủ yếu trong công trình cầu và đường; Cơ sở lập và luận chứng phương án thiết kế sơ bộ '
          'công trình cầu và đường.'},
 {'id': 59,
  'semester': 7,
  'name': 'PBL: Thiết kế công trình giao thông',
  'credits': 2.0,
  'elective': False,
  'prereq': [30, 29],
  'coreq': [58],
  'prereq_text': 'Cơ học đất; Cơ học kết cấu 1',
  'coreq_text': 'Công trình giao thông',
  'hours': {'lt': '', 'da': '', 'pbl': '2', 'th': '', 'tt': ''},
  'desc': 'Học phần này ứng dụng công nghệ thông tin để thiết kế cơ sở phương án tuyến cầu và đường của một công '
          'trình, luận chứng hiệu quả để chọn phương án tuyến.'},
 {'id': 60,
  'semester': 8,
  'name': 'Thiết kế công trình đường',
  'credits': 2.0,
  'elective': False,
  'prereq': [30, 44],
  'coreq': [],
  'prereq_text': 'Cơ học đất, Thủy văn',
  'coreq_text': '',
  'hours': {'lt': '2', 'da': '', 'pbl': '', 'th': '', 'tt': ''},
  'desc': 'Học phần cung cấp cho sinh viên kiến thức chuyên môn trong thiết kế đường ô tô: bao gồm thiết kế kỹ thuật '
          'kết cấu áo đường bê tông nhựa, bê tông xi măng và các công trình giao thông trên đường. Trên cơ sở đó sinh '
          'viên còn được giới thiệu những phương pháp cụ thể thiết kế đường ô tô, thiết kế cảnh quan , thiết kế kỹ '
          'thuật nền đường, mặt đường . Hệ thống thoát nước đường ô tô. Ngoài ra sinh viên còn được cung cấp kỹ năng '
          'sử dụng các phần mềm và ứng dụng công nghệ thông tin trong thiết kế đường ô tô.'},
 {'id': 61,
  'semester': 8,
  'name': 'Thiết kế công trình cầu',
  'credits': 2.0,
  'elective': False,
  'prereq': [29, 39, 30],
  'coreq': [],
  'prereq_text': 'Cơ học kết cấu 1, Cơ học kết cấu 2, cơ học đất',
  'coreq_text': '',
  'hours': {'lt': '2', 'da': '', 'pbl': '', 'th': '', 'tt': ''},
  'desc': 'Học phần này cung cấp các kiến thức về tính toán thiết kế công trình cầu. Môn học này đóng vai trò quan '
          'trọng trong khối kiến thức chuyên ngành qua đó tạo nền tảng về kiến thức, kỹ năng cũng như ý thức và thái '
          'độ trong học tập, lao động chuyên môn về sau của người học. Sau khi học xong, người học có thể ứng dụng '
          'ngay vào công việc thực tế như: công tác thiết kế, công tác đầu tư, quản lý, quy hoạch cơ sở hạ tầng giao '
          'thông. Úng dụng công nghệ thông tin vào trong môn học.'},
 {'id': 62,
  'semester': 8,
  'name': 'Tổ chức thi công',
  'credits': 2.0,
  'elective': False,
  'prereq': [55],
  'coreq': [],
  'prereq_text': 'Kỹ thuật thi công',
  'coreq_text': '',
  'hours': {'lt': '2', 'da': '', 'pbl': '', 'th': '', 'tt': ''},
  'desc': 'Học phần Tổ chức thi công cung cấp cho sinh viên các kiến thức về công tác lập kế hoạch các công việc của '
          'một dự án, công trình đơn vị hoặc hạng mục. Từ đó tiến hành tổ chức các công việc đã được lập. Áp dụng kiến '
          'thức và công nghệ thông tin để thiết kế bố trí, qu y hoạch mặt bằng thi công; b ố trí nhân lực, vật lực để '
          'thi công đúng kế hoạch, hiệu quả, chất lượng và an toàn.'},
 {'id': 63,
  'semester': 8,
  'name': 'PBL: Công nghệ BIM trong thi công công trình xây dựng',
  'credits': 2.0,
  'elective': False,
  'prereq': [57],
  'coreq': [62],
  'prereq_text': 'Công nghệ BIM trong xây dựng',
  'coreq_text': 'Tổ chức thi công',
  'hours': {'lt': '', 'da': '', 'pbl': '2', 'th': '', 'tt': ''},
  'desc': 'Học phần Đồ án liên môn PBL5_Công nghệ BIM trong thi công công trình xây dựng sẽ hướng dẫn sinh viên thực '
          'hành lập biện pháp kỹ thuật và tổ chức thi công cho một công trình xây dựng cụ thể. Công nghệ BIM sẽ được '
          'ứng dụng vào trong quá trình tự động hóa tính toán khối lượng (mô hình BIM 3D) và quản lý thi công (mô hình '
          'BIM 4D) .'},
 {'id': 64,
  'semester': 8,
  'name': 'Kết cấu nhà cao tầng',
  'credits': 2.0,
  'elective': False,
  'prereq': [47],
  'coreq': [],
  'prereq_text': 'Kết cấu nhà bê tông cốt thép',
  'coreq_text': '',
  'hours': {'lt': '2', 'da': '', 'pbl': '', 'th': '', 'tt': ''},
  'desc': 'Học phần Kết cấu nhà cao tầng là phần mở rộng và nâng cao của khối kiến thức về kết cấu BTCT. Học phần này '
          'trang bị cho sinh viên những kiến thức kỹ thuật về các hệ kết cấu nhà cao tầng như: hệ kết cấu sàn, khung, '
          'vách, lõi, tổ hợp… Bên cạnh đó cung cấp những kiến thức và kỹ năng trong tính toán kết cấu công trình cao '
          'tầng chịu tác dụng của các tải trọng đặc biệt, đồng thời cung cấp kĩ năng phân tích để lựa chọn phương án '
          'kết cấu thích hợp.'},
 {'id': 65,
  'semester': 8,
  'name': 'PBL: Công nghệ BIM trong thiết kế kết cấu dân dụng',
  'credits': 2.0,
  'elective': False,
  'prereq': [],
  'coreq': [64],
  'prereq_text': '',
  'coreq_text': 'Kết cấu nhà cao tầng',
  'hours': {'lt': '', 'da': '', 'pbl': '2', 'th': '', 'tt': ''},
  'desc': 'Học phần dự án liên môn PBL: Công nghệ BIM trong thiết kế kết cấu dân dụng cung cấp cho sinh viên kiến thức '
          'chuyên môn trong tính toán, thiết kế kết cấu công trình xây dựng dân dụng . Bên cạnh việc cung cấp các kiến '
          'thức, lý thuyết tính toán kết cấu xây dựng, ứng dụng các phần mềm tính toán kết cấu xây dựng, công nghệ BIM '
          'trong thiết kế kết cấu xây dựng dân dụng, sinh viên còn được trau dồi kỹ năng lập trình, viết chương trình '
          'ứng dụng tính toán thiết kế để giải quyết các bài toán cơ bản trong xây dựng.'},
 {'id': 66,
  'semester': 8,
  'name': 'Thuỷ văn công trình',
  'credits': 2.0,
  'elective': True,
  'prereq': [44],
  'coreq': [],
  'prereq_text': 'Thủy văn',
  'coreq_text': '',
  'hours': {'lt': '2', 'da': '', 'pbl': '', 'th': '', 'tt': ''},
  'desc': 'Học phần cung cấp những kiến thức khoa học cơ bản về bài toán điều tiết cấp nước, điều tiết lũ và xây dựng '
          'biểu đồ điều phối hồ chứa trong thiết kế, quản lý và vận hành . Môn học cũng sẽ cung cấp cho sinh viên kiến '
          'thức về các mô hình tính toán thủy văn và mô hình điều tiết hồ chứa giúp cho sinh viên tiếp cận được những '
          'công nghệ mới phục vụ trong nhiệm vụ thực tiễn'},
 {'id': 67,
  'semester': 8,
  'name': 'Mô hình toán thủy văn thủy lực',
  'credits': 2.0,
  'elective': True,
  'prereq': [44, 23],
  'coreq': [],
  'prereq_text': 'Thủy văn, thủy lực',
  'coreq_text': '',
  'hours': {'lt': '2', 'da': '', 'pbl': '', 'th': '', 'tt': ''},
  'desc': 'Môn học cung cấp cho sinh viên những kiến thức khoa học cơ bản về mô hình toán, các loại mô hình thủy lực, '
          'thủy văn, các cơ sở, phương pháp tính toán trong mô hình và ứng dụng của nó trong mô phỏng các quá trình '
          'thủy văn và thủy lực . Nội dung bao gồm mô hình mưa – dòng chảy, dòng chảy trong sông/kênh và ứng dụng '
          'trong tính toán dòng chảy năm, lũ, ngập lụ t …'},
 {'id': 68,
  'semester': 8,
  'name': 'Cấp nước đô thị',
  'credits': 2.0,
  'elective': True,
  'prereq': [44, 23],
  'coreq': [],
  'prereq_text': 'Thủy văn, thủy lực',
  'coreq_text': '',
  'hours': {'lt': '2', 'da': '', 'pbl': '', 'th': '', 'tt': ''},
  'desc': 'Học phần Cấp nước đô thị trang bị cho sinh viên các kiến thức cơ bản về hệ thống cấp nước trong đô thị. Nội '
          'dung học phần bao gồm các khái niệm, yêu cầu kỹ thuật và phân loại hệ thống cấp nước; xác định nhu cầu và '
          'chế độ tiêu thụ nước; tính toán, thiết kế mạng lưới cấp nước, công trình thu nước và trạm bơm. Sinh viên '
          'được tiếp cận và ứng dụng phần mềm EPANET trong phân tích và thiết kế mạng lưới cấp nước.'},
 {'id': 69,
  'semester': 8,
  'name': 'Thoát nước đô thị',
  'credits': 2.0,
  'elective': True,
  'prereq': [44, 23],
  'coreq': [],
  'prereq_text': 'Thủy văn, thủy lực',
  'coreq_text': '',
  'hours': {'lt': '2', 'da': '', 'pbl': '', 'th': '', 'tt': ''},
  'desc': 'Học phần Thoát nước đô thị cung cấp các kiến thức cơ bản và chuyên sâu về hệ thống thoát nước thải và thoát '
          'nước mưa trong đô thị, bao gồm phân loại hệ thống, cơ sở thiết kế và các nguyên lý tính toán thủy lực. Trên '
          'cơ sở đó, sinh viên được hướng dẫn xác định lưu lượng, bố trí tuyến cống và thiết kế, tính toán thủy lực '
          'mạng lưới thoát nước. Bên cạnh đó, học phần còn giới thiệu các công trình trên mạng lưới thoát nước và ứng '
          'dụng phần mềm SWMM trong mô phỏng, thiết kế và phân tích hệ thống.'},
 {'id': 70,
  'semester': 8,
  'name': 'Mô hình toán ngập lụt đô thị',
  'credits': 2.0,
  'elective': True,
  'prereq': [48],
  'coreq': [],
  'prereq_text': 'Công trình thủy',
  'coreq_text': '',
  'hours': {'lt': '2', 'da': '', 'pbl': '', 'th': '', 'tt': ''},
  'desc': 'Học phần cung cấp cho sinh viên những hiểu biết chung về ngập lụt đô thị bao gồm: Nhận diện và đánh giá rủi '
          'ro ngập lụt đô thị . Cách sử dụng mô hình toán để mô phỏng ngập lụt . Từ đó làm cơ sở quản lý ngập lụt đô '
          'thị . Mục tiêu của học phẩn Học phần giúp sinh viên h iểu nguyên lý mô hình toán , t hiết lập và hiệu chỉnh '
          'và kiểm định mô hình và ứng dụng mô hình trong bài toán thực tế'},
 {'id': 71,
  'semester': 8,
  'name': 'Công trình ven bờ',
  'credits': 2.0,
  'elective': True,
  'prereq': [48],
  'coreq': [],
  'prereq_text': 'Công trình thủy',
  'coreq_text': '',
  'hours': {'lt': '2', 'da': '', 'pbl': '', 'th': '', 'tt': ''},
  'desc': 'Học phần Công trình ven bờ cung cấp các kiến thức cơ bản về các quá trình động lực học vùng cửa sông và ven '
          'bờ như xâm nhập mặn, sóng, dòng chảy và biến đổi địa hình bờ biển. Học phần đồng thời giới thiệu các giải '
          'pháp công trình và phi công trình trong bảo vệ bờ và quy hoạch vùng ven bờ. Thông qua đó, sinh viên có khả '
          'năng áp dụng kiến thức vào thiết kế sơ bộ, đánh giá và lựa chọn phương án kỹ thuật phù hợp cho các công '
          'trình vùng cửa sông và ven biển trong thực tiễn.'},
 {'id': 72,
  'semester': 8,
  'name': 'Bê tông cốt thép dự ứng lực',
  'credits': 2.0,
  'elective': True,
  'prereq': [47],
  'coreq': [],
  'prereq_text': 'Kết cấu nhà BTCT',
  'coreq_text': '',
  'hours': {'lt': '2', 'da': '', 'pbl': '', 'th': '', 'tt': ''},
  'desc': 'Học phần trang bị cho sinh viên những kiến thức về kết cấu bê tông cốt thép dự ứng lực bao gồm: nguyên lý '
          'căng kéo, yêu cầu về vật liệu cho BTCT ứng suất trước, thép cường độ cao, tiêu chuẩn kỹ thuật áp dụng, '
          'nguyên lý thiết kế kết cấu.'},
 {'id': 73,
  'semester': 8,
  'name': 'Thiết kế nhà thép',
  'credits': 2.0,
  'elective': True,
  'prereq': [50],
  'coreq': [],
  'prereq_text': 'Cơ sở thiết kế kết cấu thép',
  'coreq_text': '',
  'hours': {'lt': '2', 'da': '', 'pbl': '', 'th': '', 'tt': ''},
  'desc': 'Đây là học phần, tiếp theo của môn học Cơ sở thiết kế kết cấu thép , cung cấp cho sinh viên những kiến thức '
          'về các kết cấu công trình thép thông dụng như : nhà công nghiệp một tầng , nhà nhịp lớn . Môn học cung cấp '
          'những kiến thức về mô hình tính , xác định tải trọng tổ hợp tải trọng, cấu tạo các kết cấu trong nhà thép . '
          'Ứng dụng công nghệ thông tin vào quá trình tính toán, thiết kế , mô phỏng kết cấu thép . Ngoài ra , môn học '
          'còn giúp cho sinh viên có các kiến thức và kỹ năng cần thiết để làm các dự án liên môn (PBL) và đồ án tốt '
          'nghiệp liên quan đến kết cấu thép .'},
 {'id': 74,
  'semester': 8,
  'name': 'Quản lý dự án công trình xây dựng',
  'credits': 2.0,
  'elective': True,
  'prereq': [56],
  'coreq': [],
  'prereq_text': 'Kinh tế xây dựng',
  'coreq_text': '',
  'hours': {'lt': '2', 'da': '', 'pbl': '', 'th': '', 'tt': ''},
  'desc': 'H ọc phần cung cấp cho sinh viên kiến thức tổng quan về quản lý hoạt động xây dựng và kiến thức cơ bản về '
          'nghiệp vụ quản lý dự án đầu tư xây dựng đối với công tác chuẩn bị đầu tư, lựa chọn nhà thầu , hợp đồng xây '
          'dựng , quản lý chất lượng công trình xây dựng , q uản lý chi phí , quản lý an toàn và môi trường xây dựng , '
          'trên cơ sở tuân thủ đúng quy định pháp luật về xây dựng hiện hành và quy định pháp luật khác liên quan .'},
 {'id': 75,
  'semester': 8,
  'name': 'Quản trị doanh nghiệp xây dựng',
  'credits': 2.0,
  'elective': True,
  'prereq': [56],
  'coreq': [],
  'prereq_text': 'Kinh tế xây dựng',
  'coreq_text': '',
  'hours': {'lt': '2', 'da': '', 'pbl': '', 'th': '', 'tt': ''},
  'desc': 'Học phần Quản trị doanh nghiệp xây dựng nhằm trang bị cho sinh viên những kiến thức cơ bản về các vấn đề '
          'sau: - Một số vấn đề mở đầu về quản trị doanh nghiệp xây dựng; - Tổ chức sản xuất kinh doanh ở các doanh '
          'nghiệp xây dựng; - Tổ chức cung ứng vật tư trong xây dựng; - Quản lý lao động và tiền lương trong các doanh '
          'nghiệp xây dựng; - Tiến bộ khoa học công nghệ trong xây dựng.'},
 {'id': 76,
  'semester': 8,
  'name': 'Công nghệ Bản sao số trong xây dựng',
  'credits': 2.0,
  'elective': True,
  'prereq': [52, 57],
  'coreq': [],
  'prereq_text': 'Ứng dụng GIS trong Xây dựng; Công nghệ BIM trong Xây dựng',
  'coreq_text': '',
  'hours': {'lt': '2', 'da': '', 'pbl': '', 'th': '', 'tt': ''},
  'desc': 'Học phần cung cấp cho sinh viên những kiến thức và kỹ năng cốt lõi về công nghệ Bản sao số (Digital Twin) '
          'trong lĩnh vực kỹ thuật xây dựng công trình thủy . Nội dung bao gồm khái niệm , kiến trúc và các thành phần '
          'của hệ thống Digital Twin; nền tảng mô hình thông tin công trình (BIM) và mô hình ba chiều (3D); hệ thống '
          'cảm biến – IoT phục vụ thu thập dữ liệu thời gian thực; nền tảng dữ liệu , mô phỏng số (CFD, FEM) và phân '
          'tích dữ liệu , trí tuệ nhân tạo (AI/ML) phục vụ ra quyết định ; cũng như các ứng dụng Digital Twin t rong '
          'vận hành , giám sát và bảo trì dự đoán các công trình thủy ( đập , hồ chứa , kênh , trạm bơm ). Học phần '
          'kết hợp giữa lý thuyết và các tình huống thực tế (case study), giúp người học tiếp cận tư duy số hóa toàn '
          'vòng đời công trình, biết khai thác các phần mềm / nền tảng phổ biến để thiết lập và vận hành một bản sao '
          'số quy mô vừa và nhỏ phục vụ chuyên ngành xây dựng công trình thủy .'},
 {'id': 77,
  'semester': 8,
  'name': 'Trí tuệ nhân tạo trong xây dựng',
  'credits': 2.0,
  'elective': True,
  'prereq': [27],
  'coreq': [],
  'prereq_text': 'Ứng dụng xác suất và thống kê trong xây dựng',
  'coreq_text': '',
  'hours': {'lt': '2', 'da': '', 'pbl': '', 'th': '', 'tt': ''},
  'desc': 'Học phần giới thiệu kiến thức cơ bản về Trí tuệ nhân tạo (AI) và Học máy (Machine Learning), tập trung vào '
          'cách xây dựng và triển khai quy trình học máy trên môi trường Python. Nội dung được thiết kế dành cho sinh '
          'viên lần đầu tiếp cận học máy, với các bộ dữ liệu thực tế được chọn lọc từ lĩnh vực xây dựng (dự báo chi '
          'phí, tiến độ, chất lượng công trình, an toàn lao động, tối ưu hóa tài nguyên…). Sinh viên sẽ học cách xử lý '
          'dữ liệu, xây dựng mô hình đơn giản và đánh giá chúng để giải quyết vấn đề thực tiễn trong ngành xây dựng.'},
 {'id': 78,
  'semester': 9,
  'name': 'Thực tập tốt nghiệp',
  'credits': 8.0,
  'elective': False,
  'prereq': [63],
  'coreq': [],
  'prereq_text': 'PBL: Công nghệ BIM trong thi công công trình xây dựng',
  'coreq_text': '',
  'hours': {'lt': '', 'da': '', 'pbl': '', 'th': '', 'tt': '8'},
  'desc': 'Học phần cung cấp cho sinh viên các kiến thức, kỹ năng thực tế cũng như hệ thống tổ chức tại các Sở ban '
          'ngành của Nhà nước, công ty, doanh nghiệp trong lĩnh vực xây dựng hay viện nghiên cứu mà sinh viên đến thực '
          'tập; Học phần này giúp sinh viên tìm hiểu các kiến thức về tính toán, thiết kế, tổ chức thi công, quản lý, '
          'vận hành các công trình xây dựng tại các đơn vị thực tập ; các vấn đề xảy ra trong suốt quá trình của dự án '
          'xây dựng; các vấn đề liên quan đến an toàn lao động và bảo vệ môi trường tại cơ sở thực tập.'},
 {'id': 79,
  'semester': 9,
  'name': 'Đồ án tốt nghiệp',
  'credits': 10.0,
  'elective': False,
  'prereq': ['ALL'],
  'coreq': [],
  'prereq_text': 'Tất cả các học phần ngoại trừ ĐATN',
  'coreq_text': '',
  'hours': {'lt': '', 'da': '10', 'pbl': '', 'th': '', 'tt': ''},
  'desc': 'Học phần Đồ án tốt nghiệp là học phần tổng hợp cuối khóa, trong đó sinh viên thực hiện một đề tài thuộc '
          'chuyên ngành dưới sự hướng dẫn của giảng viên trong thời gian 15 tuần. Trên cơ sở vận dụng các kiến thức, '
          'kỹ năng và thái độ đã tích lũy trong quá trình học tập và thực tập, sinh viên tiến hành lựa chọn và xác '
          'định vấn đề, thu thập và xử lý số liệu, xây dựng phương án, thực hiện các nội dung thiết kế, tính toán, mô '
          'phỏng hoặc nghiên cứu, đồng thời hoàn thiện báo cáo, bản vẽ và các sản phẩm liên quan. Nội dung đồ án '
          'chuyên sâu và liên ngành trong lĩnh vực kỹ thuật xây dựng để phân tích, thiết kế, thi công, quản lý, vận '
          'hành và giải quyết các vấn đề thực tiễn phức tạp của các công trình thủy, dân dụng, giao thông và hạ tầng '
          'kỹ thuật thuộc chuyên ngành Tin học xây dựng. Đồ án tốt nghiệp được thực hiện thông qua các hình thức sau '
          'đây: Đồ án thực hiện toàn thời gian tại trường dưới sự hướng dẫn của cán bộ giảng dạy của Nhà trường. Đồ án '
          'thực hiện theo hình thức kết hợp Nhà trường – Doanh nghiệp, có sự tham gia hướng dẫn của cán bộ chuyên môn '
          'tại Doanh nghiệp. Đồ án thực hiện với những kết quả từ sản phẩm nghiên cứu khoa học. Học phần kết thúc bằng '
          'việc sinh viên nộp sản phẩm và bảo vệ kết quả trước hội đồng.'}]
